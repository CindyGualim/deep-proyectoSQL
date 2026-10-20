-- Esquema 06: restaurante (espanol, nombres completos)
CREATE TABLE `categorias_plato` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(60) NOT NULL COMMENT 'Nombre de la categoria, por ejemplo entradas',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Categorias del menu';

CREATE TABLE `platos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre del plato',
  `categoria_id` INT NOT NULL COMMENT 'Categoria del menu a la que pertenece',
  `precio` DECIMAL(8,2) NOT NULL COMMENT 'Precio de venta en quetzales',
  `costo` DECIMAL(8,2) NOT NULL COMMENT 'Costo de preparacion en quetzales',
  `vegetariano` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 si el plato es vegetariano',
  `disponible` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1 si el plato se sirve actualmente',
  PRIMARY KEY (`id`),
  KEY `categoria_id` (`categoria_id`),
  CONSTRAINT `platos_ibfk_1` FOREIGN KEY (`categoria_id`) REFERENCES `categorias_plato` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Platos del menu del restaurante';

CREATE TABLE `meseros` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del mesero',
  `turno` ENUM('manana','tarde','noche') NOT NULL COMMENT 'Turno de trabajo',
  `fecha_ingreso` DATE NOT NULL COMMENT 'Fecha de ingreso al restaurante',
  `salario_base` DECIMAL(8,2) NOT NULL COMMENT 'Salario base mensual en quetzales',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Meseros que atienden las mesas';

CREATE TABLE `mesas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `numero` SMALLINT NOT NULL COMMENT 'Numero visible de la mesa',
  `capacidad` TINYINT NOT NULL COMMENT 'Numero maximo de comensales',
  `zona` ENUM('interior','terraza','barra') NOT NULL COMMENT 'Zona del local donde esta la mesa',
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Mesas del restaurante';

CREATE TABLE `pedidos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `mesa_id` INT NOT NULL COMMENT 'Mesa que hizo el pedido',
  `mesero_id` INT NOT NULL COMMENT 'Mesero que atendio el pedido',
  `fecha_hora` DATETIME NOT NULL COMMENT 'Fecha y hora en que se abrio el pedido',
  `estado` ENUM('abierto','servido','pagado','cancelado') NOT NULL COMMENT 'Estado del pedido',
  `propina` DECIMAL(8,2) NOT NULL DEFAULT 0.00 COMMENT 'Propina dejada por los comensales',
  `comensales` TINYINT NOT NULL DEFAULT 1 COMMENT 'Numero de personas en la mesa',
  PRIMARY KEY (`id`),
  KEY `mesa_id` (`mesa_id`),
  KEY `mesero_id` (`mesero_id`),
  CONSTRAINT `pedidos_ibfk_1` FOREIGN KEY (`mesa_id`) REFERENCES `mesas` (`id`),
  CONSTRAINT `pedidos_ibfk_2` FOREIGN KEY (`mesero_id`) REFERENCES `meseros` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Pedidos levantados en el restaurante';

CREATE TABLE `detalle_pedido` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `pedido_id` INT NOT NULL COMMENT 'Pedido al que pertenece la linea',
  `plato_id` INT NOT NULL COMMENT 'Plato solicitado',
  `cantidad` TINYINT NOT NULL COMMENT 'Unidades del plato en la linea',
  `precio_unitario` DECIMAL(8,2) NOT NULL COMMENT 'Precio cobrado por unidad',
  PRIMARY KEY (`id`),
  KEY `pedido_id` (`pedido_id`),
  KEY `plato_id` (`plato_id`),
  CONSTRAINT `detalle_pedido_ibfk_1` FOREIGN KEY (`pedido_id`) REFERENCES `pedidos` (`id`),
  CONSTRAINT `detalle_pedido_ibfk_2` FOREIGN KEY (`plato_id`) REFERENCES `platos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Lineas de cada pedido';
