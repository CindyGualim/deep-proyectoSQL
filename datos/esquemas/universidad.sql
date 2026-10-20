-- Esquema 04: universidad (espanol, nombres completos)
CREATE TABLE `departamentos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL COMMENT 'Nombre del departamento academico',
  `facultad` VARCHAR(100) NOT NULL COMMENT 'Facultad a la que pertenece',
  `presupuesto` DECIMAL(12,2) NOT NULL COMMENT 'Presupuesto anual asignado',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Departamentos academicos de la universidad';

CREATE TABLE `profesores` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del profesor',
  `email` VARCHAR(120) NOT NULL COMMENT 'Correo institucional',
  `departamento_id` INT NOT NULL COMMENT 'Departamento al que pertenece',
  `fecha_contratacion` DATE NOT NULL COMMENT 'Fecha de contratacion',
  `salario` DECIMAL(10,2) NOT NULL COMMENT 'Salario mensual en quetzales',
  `categoria` ENUM('auxiliar','titular','invitado') NOT NULL COMMENT 'Categoria docente',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `departamento_id` (`departamento_id`),
  CONSTRAINT `profesores_ibfk_1` FOREIGN KEY (`departamento_id`) REFERENCES `departamentos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Profesores de la universidad';

CREATE TABLE `cursos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(12) NOT NULL COMMENT 'Codigo del curso, por ejemplo CC3045',
  `nombre` VARCHAR(140) NOT NULL COMMENT 'Nombre del curso',
  `departamento_id` INT NOT NULL COMMENT 'Departamento que imparte el curso',
  `profesor_id` INT DEFAULT NULL COMMENT 'Profesor asignado, NULL si no tiene',
  `creditos` TINYINT NOT NULL COMMENT 'Creditos academicos del curso',
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `departamento_id` (`departamento_id`),
  KEY `profesor_id` (`profesor_id`),
  CONSTRAINT `cursos_ibfk_1` FOREIGN KEY (`departamento_id`) REFERENCES `departamentos` (`id`),
  CONSTRAINT `cursos_ibfk_2` FOREIGN KEY (`profesor_id`) REFERENCES `profesores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Cursos ofertados por los departamentos';

CREATE TABLE `estudiantes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `carnet` VARCHAR(10) NOT NULL COMMENT 'Numero de carnet del estudiante',
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del estudiante',
  `carrera` VARCHAR(100) NOT NULL COMMENT 'Carrera que cursa',
  `anio_ingreso` SMALLINT NOT NULL COMMENT 'Anio de ingreso a la universidad',
  `ciudad` VARCHAR(60) NOT NULL COMMENT 'Ciudad de procedencia',
  `becado` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 si tiene beca vigente',
  PRIMARY KEY (`id`),
  UNIQUE KEY `carnet` (`carnet`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Estudiantes inscritos en la universidad';

CREATE TABLE `inscripciones` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `estudiante_id` INT NOT NULL COMMENT 'Estudiante inscrito',
  `curso_id` INT NOT NULL COMMENT 'Curso en el que se inscribio',
  `ciclo` VARCHAR(10) NOT NULL COMMENT 'Ciclo academico, por ejemplo 2025-1',
  `nota_final` DECIMAL(5,2) DEFAULT NULL COMMENT 'Nota final de 0 a 100, NULL si no ha cerrado',
  `estado` ENUM('cursando','aprobado','reprobado','retirado') NOT NULL COMMENT 'Estado de la inscripcion',
  PRIMARY KEY (`id`),
  KEY `estudiante_id` (`estudiante_id`),
  KEY `curso_id` (`curso_id`),
  CONSTRAINT `inscripciones_ibfk_1` FOREIGN KEY (`estudiante_id`) REFERENCES `estudiantes` (`id`),
  CONSTRAINT `inscripciones_ibfk_2` FOREIGN KEY (`curso_id`) REFERENCES `cursos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Inscripciones de estudiantes en cursos';

CREATE TABLE `aulas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(12) NOT NULL COMMENT 'Codigo del aula',
  `edificio` VARCHAR(40) NOT NULL COMMENT 'Edificio donde se ubica',
  `capacidad` SMALLINT NOT NULL COMMENT 'Capacidad maxima de estudiantes',
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Aulas disponibles en el campus';

CREATE TABLE `horarios` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `curso_id` INT NOT NULL COMMENT 'Curso que se imparte',
  `aula_id` INT NOT NULL COMMENT 'Aula asignada',
  `dia` ENUM('lunes','martes','miercoles','jueves','viernes','sabado') NOT NULL COMMENT 'Dia de la semana',
  `hora_inicio` TIME NOT NULL COMMENT 'Hora de inicio de la sesion',
  `hora_fin` TIME NOT NULL COMMENT 'Hora de fin de la sesion',
  PRIMARY KEY (`id`),
  KEY `curso_id` (`curso_id`),
  KEY `aula_id` (`aula_id`),
  CONSTRAINT `horarios_ibfk_1` FOREIGN KEY (`curso_id`) REFERENCES `cursos` (`id`),
  CONSTRAINT `horarios_ibfk_2` FOREIGN KEY (`aula_id`) REFERENCES `aulas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Horario semanal de cada curso';
