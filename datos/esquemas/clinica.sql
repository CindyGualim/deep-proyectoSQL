-- Esquema 03: clinica (espanol, nombres abreviados)
CREATE TABLE `esp` (
  `id_esp` INT NOT NULL AUTO_INCREMENT,
  `desc_esp` VARCHAR(80) NOT NULL COMMENT 'Nombre de la especialidad medica',
  `arancel` DECIMAL(8,2) NOT NULL COMMENT 'Arancel base de la especialidad',
  PRIMARY KEY (`id_esp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Especialidades medicas de la clinica';

CREATE TABLE `pac` (
  `id_pac` INT NOT NULL AUTO_INCREMENT,
  `nom` VARCHAR(60) NOT NULL COMMENT 'Nombre del paciente',
  `ape` VARCHAR(60) NOT NULL COMMENT 'Apellido del paciente',
  `fnac` DATE NOT NULL COMMENT 'Fecha de nacimiento del paciente',
  `sexo` ENUM('M','F') NOT NULL COMMENT 'Sexo registrado del paciente',
  `tel` VARCHAR(20) DEFAULT NULL COMMENT 'Telefono de contacto',
  `seguro` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 si el paciente cuenta con seguro medico',
  PRIMARY KEY (`id_pac`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Pacientes registrados en la clinica';

CREATE TABLE `med` (
  `id_med` INT NOT NULL AUTO_INCREMENT,
  `nom` VARCHAR(60) NOT NULL COMMENT 'Nombre del medico',
  `ape` VARCHAR(60) NOT NULL COMMENT 'Apellido del medico',
  `id_esp` INT NOT NULL COMMENT 'Especialidad que ejerce el medico',
  `fing` DATE NOT NULL COMMENT 'Fecha de ingreso a la clinica',
  `tarifa` DECIMAL(8,2) NOT NULL COMMENT 'Tarifa por consulta del medico',
  PRIMARY KEY (`id_med`),
  KEY `id_esp` (`id_esp`),
  CONSTRAINT `med_ibfk_1` FOREIGN KEY (`id_esp`) REFERENCES `esp` (`id_esp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Medicos que atienden en la clinica';

CREATE TABLE `cita` (
  `id_cita` INT NOT NULL AUTO_INCREMENT,
  `id_pac` INT NOT NULL COMMENT 'Paciente atendido',
  `id_med` INT NOT NULL COMMENT 'Medico que atiende la cita',
  `fcita` DATETIME NOT NULL COMMENT 'Fecha y hora de la cita',
  `estado` ENUM('programada','atendida','cancelada','no_asistio') NOT NULL COMMENT 'Estado de la cita',
  `costo` DECIMAL(8,2) NOT NULL COMMENT 'Costo cobrado por la cita',
  PRIMARY KEY (`id_cita`),
  KEY `id_pac` (`id_pac`),
  KEY `id_med` (`id_med`),
  CONSTRAINT `cita_ibfk_1` FOREIGN KEY (`id_pac`) REFERENCES `pac` (`id_pac`),
  CONSTRAINT `cita_ibfk_2` FOREIGN KEY (`id_med`) REFERENCES `med` (`id_med`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Citas medicas agendadas';

CREATE TABLE `diag` (
  `id_diag` INT NOT NULL AUTO_INCREMENT,
  `id_cita` INT NOT NULL COMMENT 'Cita en la que se emitio el diagnostico',
  `cod_cie` VARCHAR(10) NOT NULL COMMENT 'Codigo CIE-10 del diagnostico',
  `desc_diag` VARCHAR(200) NOT NULL COMMENT 'Descripcion del diagnostico',
  `grav` ENUM('leve','moderado','severo') NOT NULL COMMENT 'Gravedad estimada del diagnostico',
  PRIMARY KEY (`id_diag`),
  KEY `id_cita` (`id_cita`),
  CONSTRAINT `diag_ibfk_1` FOREIGN KEY (`id_cita`) REFERENCES `cita` (`id_cita`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Diagnosticos emitidos en cada cita';

CREATE TABLE `rec` (
  `id_rec` INT NOT NULL AUTO_INCREMENT,
  `id_cita` INT NOT NULL COMMENT 'Cita que origino la receta',
  `farmaco` VARCHAR(120) NOT NULL COMMENT 'Nombre del farmaco recetado',
  `dosis` VARCHAR(60) NOT NULL COMMENT 'Dosis indicada al paciente',
  `dias` TINYINT NOT NULL COMMENT 'Dias de tratamiento indicados',
  PRIMARY KEY (`id_rec`),
  KEY `id_cita` (`id_cita`),
  CONSTRAINT `rec_ibfk_1` FOREIGN KEY (`id_cita`) REFERENCES `cita` (`id_cita`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Recetas emitidas en cada cita';
