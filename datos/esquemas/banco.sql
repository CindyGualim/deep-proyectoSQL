-- Esquema 12: banco (espanol, nombres completos)
CREATE TABLE `sucursales` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(80) NOT NULL COMMENT 'Nombre de la agencia bancaria',
  `ciudad` VARCHAR(60) NOT NULL COMMENT 'Ciudad donde opera la agencia',
  `fecha_apertura` DATE NOT NULL COMMENT 'Fecha de apertura de la agencia',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agencias del banco';

CREATE TABLE `clientes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del cliente',
  `dpi` VARCHAR(15) NOT NULL COMMENT 'Documento personal de identificacion',
  `fecha_nacimiento` DATE NOT NULL COMMENT 'Fecha de nacimiento del cliente',
  `ciudad` VARCHAR(60) NOT NULL COMMENT 'Ciudad de residencia',
  `ingreso_mensual` DECIMAL(12,2) NOT NULL COMMENT 'Ingreso mensual declarado en quetzales',
  `fecha_registro` DATE NOT NULL COMMENT 'Fecha en que se hizo cliente del banco',
  PRIMARY KEY (`id`),
  UNIQUE KEY `dpi` (`dpi`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Clientes del banco';

CREATE TABLE `cuentas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `numero` VARCHAR(16) NOT NULL COMMENT 'Numero de cuenta',
  `cliente_id` INT NOT NULL COMMENT 'Titular de la cuenta',
  `sucursal_id` INT NOT NULL COMMENT 'Agencia donde se abrio la cuenta',
  `tipo` ENUM('monetaria','ahorro','plazo_fijo') NOT NULL COMMENT 'Tipo de cuenta',
  `saldo` DECIMAL(14,2) NOT NULL DEFAULT 0.00 COMMENT 'Saldo actual en quetzales',
  `fecha_apertura` DATE NOT NULL COMMENT 'Fecha de apertura de la cuenta',
  `estado` ENUM('activa','inactiva','bloqueada','cerrada') NOT NULL COMMENT 'Estado de la cuenta',
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`),
  KEY `cliente_id` (`cliente_id`),
  KEY `sucursal_id` (`sucursal_id`),
  CONSTRAINT `cuentas_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`),
  CONSTRAINT `cuentas_ibfk_2` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Cuentas bancarias de los clientes';

CREATE TABLE `transacciones` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `cuenta_id` INT NOT NULL COMMENT 'Cuenta afectada por el movimiento',
  `tipo` ENUM('deposito','retiro','transferencia','pago') NOT NULL COMMENT 'Tipo de movimiento',
  `monto` DECIMAL(14,2) NOT NULL COMMENT 'Monto del movimiento en quetzales',
  `fecha_hora` DATETIME NOT NULL COMMENT 'Fecha y hora del movimiento',
  `canal` ENUM('ventanilla','cajero','app','web') NOT NULL COMMENT 'Canal por el que se hizo',
  `descripcion` VARCHAR(160) DEFAULT NULL COMMENT 'Descripcion libre del movimiento',
  PRIMARY KEY (`id`),
  KEY `cuenta_id` (`cuenta_id`),
  CONSTRAINT `transacciones_ibfk_1` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Movimientos registrados en las cuentas';

CREATE TABLE `prestamos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `cliente_id` INT NOT NULL COMMENT 'Cliente que recibe el prestamo',
  `sucursal_id` INT NOT NULL COMMENT 'Agencia que otorgo el prestamo',
  `monto` DECIMAL(14,2) NOT NULL COMMENT 'Monto otorgado en quetzales',
  `tasa_interes` DECIMAL(5,2) NOT NULL COMMENT 'Tasa de interes anual en porcentaje',
  `plazo_meses` SMALLINT NOT NULL COMMENT 'Plazo del prestamo en meses',
  `fecha_otorgamiento` DATE NOT NULL COMMENT 'Fecha en que se otorgo',
  `estado` ENUM('vigente','pagado','mora','castigado') NOT NULL COMMENT 'Estado del prestamo',
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `sucursal_id` (`sucursal_id`),
  CONSTRAINT `prestamos_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`),
  CONSTRAINT `prestamos_ibfk_2` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Prestamos otorgados a clientes';

CREATE TABLE `pagos_prestamo` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `prestamo_id` INT NOT NULL COMMENT 'Prestamo al que se abona',
  `fecha_pago` DATE NOT NULL COMMENT 'Fecha del pago',
  `monto` DECIMAL(12,2) NOT NULL COMMENT 'Monto abonado en quetzales',
  `mora` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT 'Recargo por mora cobrado',
  PRIMARY KEY (`id`),
  KEY `prestamo_id` (`prestamo_id`),
  CONSTRAINT `pagos_prestamo_ibfk_1` FOREIGN KEY (`prestamo_id`) REFERENCES `prestamos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Pagos aplicados a los prestamos';

CREATE TABLE `tarjetas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `cliente_id` INT NOT NULL COMMENT 'Titular de la tarjeta',
  `numero_enmascarado` VARCHAR(20) NOT NULL COMMENT 'Numero de tarjeta enmascarado',
  `tipo` ENUM('debito','credito') NOT NULL COMMENT 'Tipo de tarjeta',
  `limite` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT 'Limite de credito en quetzales',
  `fecha_vencimiento` DATE NOT NULL COMMENT 'Fecha de vencimiento de la tarjeta',
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  CONSTRAINT `tarjetas_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tarjetas emitidas a los clientes';
