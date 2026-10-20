-- Esquema 01: biblioteca (espanol, nombres completos)
CREATE TABLE `editoriales` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre comercial de la editorial',
  `pais` VARCHAR(60) NOT NULL COMMENT 'Pais sede de la editorial',
  `anio_fundacion` SMALLINT DEFAULT NULL COMMENT 'Anio de fundacion',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Editoriales que publican los libros del catalogo';

CREATE TABLE `autores` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del autor',
  `nacionalidad` VARCHAR(60) NOT NULL COMMENT 'Nacionalidad del autor',
  `fecha_nacimiento` DATE DEFAULT NULL COMMENT 'Fecha de nacimiento',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Autores de los libros del catalogo';

CREATE TABLE `libros` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `titulo` VARCHAR(200) NOT NULL COMMENT 'Titulo del libro',
  `isbn` VARCHAR(20) NOT NULL COMMENT 'ISBN-13 del ejemplar',
  `autor_id` INT NOT NULL COMMENT 'Autor principal del libro',
  `editorial_id` INT NOT NULL COMMENT 'Editorial que lo publico',
  `anio_publicacion` SMALLINT NOT NULL COMMENT 'Anio de publicacion',
  `paginas` SMALLINT NOT NULL COMMENT 'Numero de paginas',
  `precio` DECIMAL(8,2) NOT NULL COMMENT 'Precio de reposicion en quetzales',
  `genero` ENUM('novela','ensayo','poesia','tecnico','infantil') NOT NULL COMMENT 'Genero literario',
  `ejemplares` TINYINT NOT NULL DEFAULT 1 COMMENT 'Ejemplares disponibles en el sistema',
  PRIMARY KEY (`id`),
  UNIQUE KEY `isbn` (`isbn`),
  KEY `autor_id` (`autor_id`),
  KEY `editorial_id` (`editorial_id`),
  CONSTRAINT `libros_ibfk_1` FOREIGN KEY (`autor_id`) REFERENCES `autores` (`id`),
  CONSTRAINT `libros_ibfk_2` FOREIGN KEY (`editorial_id`) REFERENCES `editoriales` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Catalogo de libros de la biblioteca';

CREATE TABLE `sucursales` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(80) NOT NULL COMMENT 'Nombre de la sucursal',
  `ciudad` VARCHAR(60) NOT NULL COMMENT 'Ciudad donde opera',
  `direccion` VARCHAR(160) NOT NULL COMMENT 'Direccion fisica',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Sucursales de la red de bibliotecas';

CREATE TABLE `socios` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del socio',
  `email` VARCHAR(120) NOT NULL COMMENT 'Correo de contacto',
  `fecha_alta` DATE NOT NULL COMMENT 'Fecha en que se afilio',
  `ciudad` VARCHAR(60) NOT NULL COMMENT 'Ciudad de residencia',
  `activo` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1 si la membresia esta vigente',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Socios inscritos en la biblioteca';

CREATE TABLE `prestamos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `libro_id` INT NOT NULL COMMENT 'Libro prestado',
  `socio_id` INT NOT NULL COMMENT 'Socio que realizo el prestamo',
  `sucursal_id` INT NOT NULL COMMENT 'Sucursal donde se entrego el libro',
  `fecha_prestamo` DATE NOT NULL COMMENT 'Fecha de salida del libro',
  `fecha_devolucion` DATE DEFAULT NULL COMMENT 'Fecha real de devolucion, NULL si sigue prestado',
  `multa` DECIMAL(6,2) NOT NULL DEFAULT 0.00 COMMENT 'Multa por retraso en quetzales',
  PRIMARY KEY (`id`),
  KEY `libro_id` (`libro_id`),
  KEY `socio_id` (`socio_id`),
  KEY `sucursal_id` (`sucursal_id`),
  CONSTRAINT `prestamos_ibfk_1` FOREIGN KEY (`libro_id`) REFERENCES `libros` (`id`),
  CONSTRAINT `prestamos_ibfk_2` FOREIGN KEY (`socio_id`) REFERENCES `socios` (`id`),
  CONSTRAINT `prestamos_ibfk_3` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Prestamos de libros a socios';

CREATE TABLE `reservas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `libro_id` INT NOT NULL COMMENT 'Libro reservado',
  `socio_id` INT NOT NULL COMMENT 'Socio que reserva',
  `fecha_reserva` DATE NOT NULL COMMENT 'Fecha en que se hizo la reserva',
  `estado` ENUM('pendiente','atendida','cancelada') NOT NULL DEFAULT 'pendiente' COMMENT 'Estado de la reserva',
  PRIMARY KEY (`id`),
  KEY `libro_id` (`libro_id`),
  KEY `socio_id` (`socio_id`),
  CONSTRAINT `reservas_ibfk_1` FOREIGN KEY (`libro_id`) REFERENCES `libros` (`id`),
  CONSTRAINT `reservas_ibfk_2` FOREIGN KEY (`socio_id`) REFERENCES `socios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Reservas de libros que estan prestados';
