-- Esquema 09: inmobiliaria (espanol, nombres completos)
CREATE TABLE `zonas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(80) NOT NULL COMMENT 'Nombre de la zona o colonia',
  `ciudad` VARCHAR(60) NOT NULL COMMENT 'Ciudad donde esta la zona',
  `precio_m2` DECIMAL(10,2) NOT NULL COMMENT 'Precio promedio por metro cuadrado',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Zonas donde la inmobiliaria tiene propiedades';

CREATE TABLE `agentes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del agente',
  `email` VARCHAR(120) NOT NULL COMMENT 'Correo de contacto del agente',
  `comision_pct` DECIMAL(5,2) NOT NULL COMMENT 'Porcentaje de comision que cobra',
  `fecha_ingreso` DATE NOT NULL COMMENT 'Fecha de ingreso a la inmobiliaria',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agentes de bienes raices';

CREATE TABLE `clientes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del cliente',
  `telefono` VARCHAR(20) NOT NULL COMMENT 'Telefono de contacto',
  `presupuesto_max` DECIMAL(12,2) NOT NULL COMMENT 'Presupuesto maximo declarado',
  `tipo` ENUM('comprador','arrendatario','inversionista') NOT NULL COMMENT 'Tipo de cliente',
  `fecha_registro` DATE NOT NULL COMMENT 'Fecha en que se registro el cliente',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Clientes interesados en propiedades';

CREATE TABLE `propiedades` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(12) NOT NULL COMMENT 'Codigo interno de la propiedad',
  `zona_id` INT NOT NULL COMMENT 'Zona donde se ubica',
  `tipo` ENUM('casa','apartamento','terreno','local') NOT NULL COMMENT 'Tipo de inmueble',
  `habitaciones` TINYINT NOT NULL DEFAULT 0 COMMENT 'Numero de habitaciones',
  `banos` TINYINT NOT NULL DEFAULT 0 COMMENT 'Numero de banos',
  `metros2` DECIMAL(8,2) NOT NULL COMMENT 'Area en metros cuadrados',
  `precio` DECIMAL(12,2) NOT NULL COMMENT 'Precio de lista en quetzales',
  `estado` ENUM('disponible','reservada','vendida','alquilada') NOT NULL COMMENT 'Estado comercial',
  `fecha_publicacion` DATE NOT NULL COMMENT 'Fecha en que se publico',
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `zona_id` (`zona_id`),
  CONSTRAINT `propiedades_ibfk_1` FOREIGN KEY (`zona_id`) REFERENCES `zonas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Propiedades en cartera';

CREATE TABLE `visitas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `propiedad_id` INT NOT NULL COMMENT 'Propiedad visitada',
  `cliente_id` INT NOT NULL COMMENT 'Cliente que visito',
  `agente_id` INT NOT NULL COMMENT 'Agente que acompano la visita',
  `fecha` DATETIME NOT NULL COMMENT 'Fecha y hora de la visita',
  `calificacion` TINYINT DEFAULT NULL COMMENT 'Calificacion del cliente de 1 a 5',
  PRIMARY KEY (`id`),
  KEY `propiedad_id` (`propiedad_id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `agente_id` (`agente_id`),
  CONSTRAINT `visitas_ibfk_1` FOREIGN KEY (`propiedad_id`) REFERENCES `propiedades` (`id`),
  CONSTRAINT `visitas_ibfk_2` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`),
  CONSTRAINT `visitas_ibfk_3` FOREIGN KEY (`agente_id`) REFERENCES `agentes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Visitas de clientes a propiedades';

CREATE TABLE `contratos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `propiedad_id` INT NOT NULL COMMENT 'Propiedad del contrato',
  `cliente_id` INT NOT NULL COMMENT 'Cliente que firma',
  `agente_id` INT NOT NULL COMMENT 'Agente que cerro la operacion',
  `tipo` ENUM('venta','alquiler') NOT NULL COMMENT 'Tipo de contrato',
  `monto` DECIMAL(12,2) NOT NULL COMMENT 'Monto pactado en quetzales',
  `fecha_firma` DATE NOT NULL COMMENT 'Fecha de firma del contrato',
  PRIMARY KEY (`id`),
  KEY `propiedad_id` (`propiedad_id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `agente_id` (`agente_id`),
  CONSTRAINT `contratos_ibfk_1` FOREIGN KEY (`propiedad_id`) REFERENCES `propiedades` (`id`),
  CONSTRAINT `contratos_ibfk_2` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`),
  CONSTRAINT `contratos_ibfk_3` FOREIGN KEY (`agente_id`) REFERENCES `agentes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Contratos de venta y alquiler cerrados';
