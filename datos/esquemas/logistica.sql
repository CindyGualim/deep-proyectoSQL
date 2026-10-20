-- Esquema 10: logistica (espanol e ingles mezclados)
CREATE TABLE `clientes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `razon_social` VARCHAR(140) NOT NULL COMMENT 'Razon social de la empresa cliente',
  `nit` VARCHAR(15) NOT NULL COMMENT 'Numero de identificacion tributaria',
  `ciudad` VARCHAR(60) NOT NULL COMMENT 'Ciudad del cliente',
  `fecha_alta` DATE NOT NULL COMMENT 'Fecha en que se dio de alta el cliente',
  PRIMARY KEY (`id`),
  UNIQUE KEY `nit` (`nit`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Empresas que contratan los envios';

CREATE TABLE `vehiculos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `placa` VARCHAR(10) NOT NULL COMMENT 'Placa del vehiculo',
  `tipo` ENUM('moto','panel','camion','trailer') NOT NULL COMMENT 'Tipo de vehiculo',
  `capacidad_kg` DECIMAL(10,2) NOT NULL COMMENT 'Capacidad de carga en kilogramos',
  `anio` SMALLINT NOT NULL COMMENT 'Anio del vehiculo',
  PRIMARY KEY (`id`),
  UNIQUE KEY `placa` (`placa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Flota de vehiculos de reparto';

CREATE TABLE `conductores` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del conductor',
  `licencia` VARCHAR(20) NOT NULL COMMENT 'Numero de licencia de conducir',
  `vehiculo_id` INT DEFAULT NULL COMMENT 'Vehiculo asignado, NULL si no tiene',
  `fecha_ingreso` DATE NOT NULL COMMENT 'Fecha de ingreso a la empresa',
  `salario` DECIMAL(10,2) NOT NULL COMMENT 'Salario mensual en quetzales',
  PRIMARY KEY (`id`),
  UNIQUE KEY `licencia` (`licencia`),
  KEY `vehiculo_id` (`vehiculo_id`),
  CONSTRAINT `conductores_ibfk_1` FOREIGN KEY (`vehiculo_id`) REFERENCES `vehiculos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Conductores de la empresa';

CREATE TABLE `rutas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `origen` VARCHAR(60) NOT NULL COMMENT 'Ciudad de origen de la ruta',
  `destino` VARCHAR(60) NOT NULL COMMENT 'Ciudad de destino de la ruta',
  `distancia_km` DECIMAL(8,2) NOT NULL COMMENT 'Distancia en kilometros',
  `horas_estimadas` DECIMAL(5,2) NOT NULL COMMENT 'Tiempo estimado de recorrido en horas',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Rutas de distribucion disponibles';

CREATE TABLE `envios` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `guia` VARCHAR(16) NOT NULL COMMENT 'Numero de guia del envio',
  `cliente_id` INT NOT NULL COMMENT 'Cliente que contrato el envio',
  `ruta_id` INT NOT NULL COMMENT 'Ruta utilizada',
  `conductor_id` INT NOT NULL COMMENT 'Conductor responsable',
  `fecha_envio` DATE NOT NULL COMMENT 'Fecha de salida del envio',
  `fecha_entrega` DATE DEFAULT NULL COMMENT 'Fecha de entrega, NULL si sigue en transito',
  `peso_kg` DECIMAL(10,2) NOT NULL COMMENT 'Peso total del envio en kilogramos',
  `costo` DECIMAL(10,2) NOT NULL COMMENT 'Costo cobrado al cliente',
  `estado` ENUM('en_bodega','en_transito','entregado','devuelto') NOT NULL COMMENT 'Estado del envio',
  PRIMARY KEY (`id`),
  UNIQUE KEY `guia` (`guia`),
  KEY `cliente_id` (`cliente_id`),
  KEY `ruta_id` (`ruta_id`),
  KEY `conductor_id` (`conductor_id`),
  CONSTRAINT `envios_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`),
  CONSTRAINT `envios_ibfk_2` FOREIGN KEY (`ruta_id`) REFERENCES `rutas` (`id`),
  CONSTRAINT `envios_ibfk_3` FOREIGN KEY (`conductor_id`) REFERENCES `conductores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Envios gestionados por la empresa';

CREATE TABLE `incidencias` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `envio_id` INT NOT NULL COMMENT 'Envio afectado por la incidencia',
  `tipo` ENUM('retraso','dano','perdida','direccion_errada') NOT NULL COMMENT 'Tipo de incidencia',
  `descripcion` VARCHAR(200) NOT NULL COMMENT 'Detalle de lo ocurrido',
  `fecha` DATE NOT NULL COMMENT 'Fecha en que se registro la incidencia',
  `costo_asociado` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT 'Costo que genero la incidencia',
  PRIMARY KEY (`id`),
  KEY `envio_id` (`envio_id`),
  CONSTRAINT `incidencias_ibfk_1` FOREIGN KEY (`envio_id`) REFERENCES `envios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Incidencias registradas durante los envios';
