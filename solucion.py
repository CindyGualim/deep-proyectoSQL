"""Contrato de entrega del Proyecto 3: texto a SQL.

Expone generar_sql(esquema, pregunta, ejecutar=None) -> str, que devuelve una
sola consulta MySQL, SELECT o WITH ... SELECT.

El modelo y el adapter se leen de config.json. Con "usar_adapter": false se
carga el modelo base con exactamente el mismo prompt, que es la version contra
la que se mide el aporte del fine-tuning.

La generacion es determinista: do_sample=False, un solo haz y semilla fija.

El argumento `ejecutar` se acepta por contrato pero esta version no lo usa; la
correccion de la consulta con sus resultados es el experimento de inferencia y
vive en el modulo de autocorreccion, que se activa desde config.json.
"""

import json
import os
import pathlib
import re
import threading

RAIZ = pathlib.Path(__file__).resolve().parent
CONFIG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))

SEMILLA = int(CONFIG.get("semilla", 2026))
MAX_TOKENS_NUEVOS = 320

INSTRUCCIONES = """Eres un experto en MySQL 8.4. Recibes el esquema de una base de datos y una pregunta en espanol, y escribes UNA sola consulta MySQL que la responda.

Reglas:
- Responde unicamente con la consulta. Sin explicaciones y sin formato markdown.
- La consulta empieza por SELECT o por WITH, y es una sola sentencia.
- Usa solamente tablas y columnas que aparezcan en el esquema, con su nombre exacto.
- Esta activo ONLY_FULL_GROUP_BY: toda columna no agregada del SELECT debe estar en el GROUP BY.
- Devuelve exactamente las columnas que pide la pregunta, en el orden en que las pide.
- Usa ORDER BY solo cuando la pregunta pida un orden o los primeros N resultados.
- Redondea con ROUND(x, 2) cuando la pregunta pida decimales.
- Nunca modifiques la base: no uses INSERT, UPDATE, DELETE ni DDL."""

_modelo = None
_tokenizer = None
_candado = threading.Lock()


# --------------------------------------------------------------------------
# Carga del modelo
# --------------------------------------------------------------------------

def _hay_adapter(ruta):
    """El adapter solo se usa si realmente hay pesos entrenados en la carpeta."""
    carpeta = RAIZ / ruta
    return (carpeta / "adapter_config.json").is_file()


def cargar_modelo():
    """Carga modelo y tokenizer una sola vez. Tope de 5 minutos por contrato."""
    global _modelo, _tokenizer
    with _candado:
        if _modelo is not None:
            return _modelo, _tokenizer

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

        set_seed(SEMILLA)
        torch.manual_seed(SEMILLA)

        nombre = CONFIG["modelo_base"]
        tokenizer = AutoTokenizer.from_pretrained(nombre)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"

        modelo = AutoModelForCausalLM.from_pretrained(
            nombre,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            low_cpu_mem_usage=True,
        )

        ruta_adapter = CONFIG.get("adapter", "adapter/")
        if CONFIG.get("usar_adapter", True):
            if _hay_adapter(ruta_adapter):
                from peft import PeftModel

                modelo = PeftModel.from_pretrained(modelo, str(RAIZ / ruta_adapter))
                modelo = modelo.merge_and_unload()
            else:
                print("[solucion] usar_adapter=true pero %s no tiene pesos; "
                      "se usa el modelo base" % ruta_adapter)

        modelo.eval()
        modelo.generation_config.do_sample = False
        modelo.generation_config.temperature = None
        modelo.generation_config.top_p = None
        modelo.generation_config.top_k = None

        _modelo, _tokenizer = modelo, tokenizer
        return _modelo, _tokenizer


# --------------------------------------------------------------------------
# Prompt y extraccion de la consulta
# --------------------------------------------------------------------------

def construir_prompt(tokenizer, esquema, pregunta):
    mensajes = [
        {"role": "system", "content": INSTRUCCIONES},
        {"role": "user", "content":
            "Esquema de la base de datos:\n\n%s\n\nPregunta: %s" % (esquema.strip(), pregunta.strip())},
    ]
    return tokenizer.apply_chat_template(
        mensajes, tokenize=False, add_generation_prompt=True
    )


ESCRITURA = re.compile(
    r"^\s*(insert|update|delete|drop|alter|create|truncate|replace|grant|set)\b",
    re.IGNORECASE,
)


def extraer_sql(texto):
    """Deja una sola sentencia SELECT a partir de lo que genero el modelo."""
    limpio = texto.strip()
    limpio = re.sub(r"```(?:sql|mysql)?", "", limpio, flags=re.IGNORECASE).replace("```", "")

    inicio = re.search(r"\b(select|with)\b", limpio, flags=re.IGNORECASE)
    if not inicio:
        # Sin consulta utilizable: se devuelve algo inofensivo antes que
        # arriesgar una sentencia que escriba en la base.
        return "SELECT 1"
    limpio = limpio[inicio.start():]

    # Una sola sentencia: se corta en el primer punto y coma y en el primer
    # salto de linea doble, que es donde los modelos suelen empezar a explicar.
    limpio = limpio.split(";")[0]
    limpio = re.split(r"\n\s*\n", limpio)[0]

    limpio = re.sub(r"[ \t]+", " ", limpio).strip()
    if ESCRITURA.match(limpio):
        return "SELECT 1"
    return limpio


# --------------------------------------------------------------------------
# Contrato
# --------------------------------------------------------------------------

def generar_sql(esquema: str, pregunta: str, ejecutar=None) -> str:
    modelo, tokenizer = cargar_modelo()
    import torch

    prompt = construir_prompt(tokenizer, esquema, pregunta)
    entradas = tokenizer(prompt, return_tensors="pt").to(modelo.device)

    with torch.no_grad():
        salida = modelo.generate(
            **entradas,
            max_new_tokens=MAX_TOKENS_NUEVOS,
            do_sample=False,
            num_beams=1,
            pad_token_id=tokenizer.pad_token_id,
        )

    generado = tokenizer.decode(
        salida[0][entradas["input_ids"].shape[1]:], skip_special_tokens=True
    )
    return extraer_sql(generado)


if __name__ == "__main__":
    ruta = RAIZ / "datos" / "validacion" / "esquemas_show_create.json"
    esquemas = json.loads(ruta.read_text(encoding="utf-8"))
    preguntas = [
        ("veterinaria", "Cuantas mascotas hay registradas en la clinica? Devuelve solo el total."),
        ("hotel", "Cuantas reservas tiene cada tipo de habitacion? Devuelve el nombre del tipo y la cantidad."),
    ]
    for base, pregunta in preguntas:
        print("\n[%s] %s" % (base, pregunta))
        print("  ->", generar_sql(esquemas[base], pregunta))
