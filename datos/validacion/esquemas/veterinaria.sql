-- Validacion 01: veterinaria (espanol). No aparece en el entrenamiento.
CREATE TABLE `especies` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(60) NOT NULL COMMENT 'Nombre de la especie, por ejemplo canino',
  `esperanza_vida` TINYINT NOT NULL COMMENT 'Esperanza de vida en anios',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Especies que atiende la clinica veterinaria';

CREATE TABLE `duenos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del dueno',
  `telefono` VARCHAR(20) NOT NULL COMMENT 'Telefono de contacto',
  `ciudad` VARCHAR(60) NOT NULL COMMENT 'Ciudad de residencia del dueno',
  `fecha_registro` DATE NOT NULL COMMENT 'Fecha en que se registro en la clinica',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Duenos de las mascotas atendidas';

CREATE TABLE `mascotas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(60) NOT NULL COMMENT 'Nombre de la mascota',
  `dueno_id` INT NOT NULL COMMENT 'Dueno de la mascota',
  `especie_id` INT NOT NULL COMMENT 'Especie de la mascota',
  `fecha_nacimiento` DATE NOT NULL COMMENT 'Fecha de nacimiento de la mascota',
  `peso_kg` DECIMAL(6,2) NOT NULL COMMENT 'Peso actual en kilogramos',
  `sexo` ENUM('macho','hembra') NOT NULL COMMENT 'Sexo de la mascota',
  `esterilizado` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 si la mascota esta esterilizada',
  PRIMARY KEY (`id`),
  KEY `dueno_id` (`dueno_id`),
  KEY `especie_id` (`especie_id`),
  CONSTRAINT `mascotas_ibfk_1` FOREIGN KEY (`dueno_id`) REFERENCES `duenos` (`id`),
  CONSTRAINT `mascotas_ibfk_2` FOREIGN KEY (`especie_id`) REFERENCES `especies` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Mascotas registradas en la clinica';

CREATE TABLE `veterinarios` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del veterinario',
  `colegiado` VARCHAR(12) NOT NULL COMMENT 'Numero de colegiado profesional',
  `fecha_ingreso` DATE NOT NULL COMMENT 'Fecha de ingreso a la clinica',
  `honorario_hora` DECIMAL(8,2) NOT NULL COMMENT 'Honorario por hora en quetzales',
  PRIMARY KEY (`id`),
  UNIQUE KEY `colegiado` (`colegiado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Veterinarios que atienden en la clinica';

CREATE TABLE `consultas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `mascota_id` INT NOT NULL COMMENT 'Mascota atendida en la consulta',
  `veterinario_id` INT NOT NULL COMMENT 'Veterinario que atendio',
  `fecha` DATE NOT NULL COMMENT 'Fecha de la consulta',
  `motivo` ENUM('control','emergencia','cirugia','vacunacion') NOT NULL COMMENT 'Motivo de la consulta',
  `costo` DECIMAL(10,2) NOT NULL COMMENT 'Costo cobrado por la consulta en quetzales',
  `duracion_min` SMALLINT NOT NULL COMMENT 'Duracion de la consulta en minutos',
  PRIMARY KEY (`id`),
  KEY `mascota_id` (`mascota_id`),
  KEY `veterinario_id` (`veterinario_id`),
  CONSTRAINT `consultas_ibfk_1` FOREIGN KEY (`mascota_id`) REFERENCES `mascotas` (`id`),
  CONSTRAINT `consultas_ibfk_2` FOREIGN KEY (`veterinario_id`) REFERENCES `veterinarios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Consultas atendidas en la clinica';

CREATE TABLE `vacunas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `consulta_id` INT NOT NULL COMMENT 'Consulta en la que se aplico la vacuna',
  `nombre_vacuna` VARCHAR(80) NOT NULL COMMENT 'Nombre de la vacuna aplicada',
  `lote` VARCHAR(20) NOT NULL COMMENT 'Numero de lote de la vacuna',
  `proxima_dosis` DATE DEFAULT NULL COMMENT 'Fecha de la siguiente dosis, NULL si no aplica',
  PRIMARY KEY (`id`),
  KEY `consulta_id` (`consulta_id`),
  CONSTRAINT `vacunas_ibfk_1` FOREIGN KEY (`consulta_id`) REFERENCES `consultas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Vacunas aplicadas durante las consultas';

CREATE TABLE `tratamientos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `consulta_id` INT NOT NULL COMMENT 'Consulta que origino el tratamiento',
  `descripcion` VARCHAR(200) NOT NULL COMMENT 'Descripcion del tratamiento indicado',
  `dias` TINYINT NOT NULL COMMENT 'Duracion del tratamiento en dias',
  `precio` DECIMAL(10,2) NOT NULL COMMENT 'Precio del tratamiento en quetzales',
  PRIMARY KEY (`id`),
  KEY `consulta_id` (`consulta_id`),
  CONSTRAINT `tratamientos_ibfk_1` FOREIGN KEY (`consulta_id`) REFERENCES `consultas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tratamientos indicados en cada consulta';
