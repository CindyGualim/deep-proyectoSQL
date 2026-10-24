"""Entrena un adapter LoRA sobre Qwen2.5-Coder para texto a SQL.

El prompt es exactamente el que usa solucion.py en inferencia: se importa de
alli en vez de copiarlo, porque entrenar con un formato y generar con otro es la
forma mas silenciosa de perder puntos.

La perdida se calcula solo sobre la consulta. El esquema y la pregunta se
enmascaran con -100 para que el modelo no gaste capacidad aprendiendo a repetir
el enunciado.

Uso:
    python scripts/entrenar.py --etiqueta r8  --rank 8
    python scripts/entrenar.py --etiqueta r32 --rank 32

Las dos corridas difieren en un solo factor, el rank; alpha, learning rate,
epocas y modulos objetivo se mantienen fijos.
"""

import argparse
import csv
import json
import pathlib
import sys
import time

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import solucion  # noqa: E402

MAX_LARGO = 2048


def cargar_ejemplos(ruta_pares, ruta_esquemas):
    esquemas = json.loads(pathlib.Path(ruta_esquemas).read_text(encoding="utf-8"))
    pares = [json.loads(l) for l in open(ruta_pares, encoding="utf-8")]
    return pares, esquemas


def construir_dataset(pares, esquemas, tokenizer):
    """Devuelve input_ids y labels con el prompt enmascarado."""
    ejemplos, descartados = [], 0
    for par in pares:
        prompt = solucion.construir_prompt(tokenizer, esquemas[par["base"]], par["pregunta"])
        respuesta = par["sql"].strip() + tokenizer.eos_token

        ids_prompt = tokenizer(prompt, add_special_tokens=False)["input_ids"]
        ids_respuesta = tokenizer(respuesta, add_special_tokens=False)["input_ids"]
        ids = ids_prompt + ids_respuesta
        if len(ids) > MAX_LARGO:
            descartados += 1
            continue
        etiquetas = [-100] * len(ids_prompt) + list(ids_respuesta)
        ejemplos.append({"input_ids": ids, "labels": etiquetas,
                         "attention_mask": [1] * len(ids)})
    if descartados:
        print("ejemplos descartados por pasar de %d tokens: %d" % (MAX_LARGO, descartados))
    return ejemplos


class Colador:
    """Rellena cada lote a la longitud de su ejemplo mas largo."""

    def __init__(self, pad_id):
        self.pad_id = pad_id

    def __call__(self, lote):
        import torch

        largo = max(len(e["input_ids"]) for e in lote)
        ids, etiquetas, mascara = [], [], []
        for e in lote:
            relleno = largo - len(e["input_ids"])
            ids.append(e["input_ids"] + [self.pad_id] * relleno)
            etiquetas.append(e["labels"] + [-100] * relleno)
            mascara.append(e["attention_mask"] + [0] * relleno)
        return {"input_ids": torch.tensor(ids),
                "labels": torch.tensor(etiquetas),
                "attention_mask": torch.tensor(mascara)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etiqueta", required=True, help="Nombre de la corrida")
    parser.add_argument("--rank", type=int, default=16, help="r de LoRA")
    parser.add_argument("--alpha", type=int, default=32, help="lora_alpha")
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--epocas", type=float, default=2.0)
    parser.add_argument("--lote", type=int, default=2)
    parser.add_argument("--acumular", type=int, default=8)
    parser.add_argument("--qlora", action="store_true",
                        help="Carga el modelo base en 4 bits")
    parser.add_argument("--pares", default=str(RAIZ / "datos/entrenamiento.jsonl"))
    parser.add_argument("--dev", default=str(RAIZ / "datos/dev.jsonl"))
    parser.add_argument("--esquemas", default=str(RAIZ / "datos/esquemas_show_create.json"))
    parser.add_argument("--salida", default=None,
                        help="Carpeta del adapter, por defecto adapter_<etiqueta>/")
    args = parser.parse_args()

    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                              TrainingArguments, set_seed)

    semilla = solucion.SEMILLA
    set_seed(semilla)

    nombre = solucion.CONFIG["modelo_base"]
    tokenizer = AutoTokenizer.from_pretrained(nombre)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    carga = {"dtype": torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16}
    if args.qlora:
        from transformers import BitsAndBytesConfig

        carga["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
    modelo = AutoModelForCausalLM.from_pretrained(nombre, device_map="auto", **carga)
    modelo.config.use_cache = False
    modelo.gradient_checkpointing_enable()
    modelo.enable_input_require_grads()

    lora = LoraConfig(
        r=args.rank,
        lora_alpha=args.alpha,
        lora_dropout=args.dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
    modelo = get_peft_model(modelo, lora)
    entrenables = sum(p.numel() for p in modelo.parameters() if p.requires_grad)
    totales = sum(p.numel() for p in modelo.parameters())
    print("parametros entrenables: %s de %s (%.3f%%)"
          % (f"{entrenables:,}", f"{totales:,}", 100 * entrenables / totales))

    pares, esquemas = cargar_ejemplos(args.pares, args.esquemas)
    dev, _ = cargar_ejemplos(args.dev, args.esquemas)
    entrenamiento = construir_dataset(pares, esquemas, tokenizer)
    validacion = construir_dataset(dev, esquemas, tokenizer)
    print("ejemplos: %d de entrenamiento, %d de dev" % (len(entrenamiento), len(validacion)))

    salida = args.salida or str(RAIZ / ("adapter_%s" % args.etiqueta))
    argumentos = TrainingArguments(
        output_dir=str(RAIZ / "outputs" / args.etiqueta),
        per_device_train_batch_size=args.lote,
        per_device_eval_batch_size=args.lote,
        gradient_accumulation_steps=args.acumular,
        num_train_epochs=args.epocas,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="no",
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        optim="adamw_torch",
        report_to=[],
        seed=semilla,
        data_seed=semilla,
    )

    entrenador = Trainer(
        model=modelo,
        args=argumentos,
        train_dataset=entrenamiento,
        eval_dataset=validacion,
        data_collator=Colador(tokenizer.pad_token_id),
    )

    inicio = time.time()
    entrenador.train()
    minutos = (time.time() - inicio) / 60

    modelo.save_pretrained(salida)
    tokenizer.save_pretrained(salida)
    print("\nadapter guardado en %s" % salida)
    print("tiempo de entrenamiento: %.1f minutos" % minutos)

    _guardar_historial(args, entrenador.state.log_history, entrenables, minutos)


def _guardar_historial(args, historial, entrenables, minutos):
    """Guarda las curvas de loss y la ficha de la corrida."""
    carpeta = RAIZ / "resultados"
    carpeta.mkdir(exist_ok=True)

    ruta = carpeta / ("loss_%s.csv" % args.etiqueta)
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(["paso", "epoca", "loss_entrenamiento", "loss_validacion"])
        for registro in historial:
            escritor.writerow([registro.get("step"), registro.get("epoch"),
                               registro.get("loss"), registro.get("eval_loss")])

    ficha = {
        "etiqueta": args.etiqueta, "rank": args.rank, "alpha": args.alpha,
        "dropout": args.dropout, "learning_rate": args.lr, "epocas": args.epocas,
        "lote_efectivo": args.lote * args.acumular, "qlora": args.qlora,
        "parametros_entrenables": entrenables, "minutos": round(minutos, 1),
        "loss_final_entrenamiento": next(
            (r["loss"] for r in reversed(historial) if "loss" in r), None),
        "loss_final_validacion": next(
            (r["eval_loss"] for r in reversed(historial) if "eval_loss" in r), None),
    }
    (carpeta / ("corrida_%s.json" % args.etiqueta)).write_text(
        json.dumps(ficha, indent=1, ensure_ascii=False), encoding="utf-8")
    print("curvas en %s" % ruta)


if __name__ == "__main__":
    main()
