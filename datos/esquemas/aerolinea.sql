-- Esquema 07: aerolinea (espanol e ingles mezclados)
CREATE TABLE `aeropuertos` (
  `iata` CHAR(3) NOT NULL COMMENT 'Codigo IATA de tres letras',
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre del aeropuerto',
  `ciudad` VARCHAR(80) NOT NULL COMMENT 'Ciudad donde se ubica',
  `pais` VARCHAR(60) NOT NULL COMMENT 'Pais donde se ubica',
  PRIMARY KEY (`iata`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Aeropuertos que opera la aerolinea';

CREATE TABLE `aviones` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `matricula` VARCHAR(10) NOT NULL COMMENT 'Matricula de la aeronave',
  `modelo` VARCHAR(40) NOT NULL COMMENT 'Modelo de la aeronave',
  `capacidad` SMALLINT NOT NULL COMMENT 'Numero de asientos',
  `anio` SMALLINT NOT NULL COMMENT 'Anio de fabricacion',
  PRIMARY KEY (`id`),
  UNIQUE KEY `matricula` (`matricula`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Flota de aeronaves';

CREATE TABLE `vuelos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `numero` VARCHAR(8) NOT NULL COMMENT 'Numero de vuelo, por ejemplo AV204',
  `origen` CHAR(3) NOT NULL COMMENT 'Aeropuerto de salida',
  `destino` CHAR(3) NOT NULL COMMENT 'Aeropuerto de llegada',
  `avion_id` INT NOT NULL COMMENT 'Aeronave asignada al vuelo',
  `salida` DATETIME NOT NULL COMMENT 'Fecha y hora de salida programada',
  `llegada` DATETIME NOT NULL COMMENT 'Fecha y hora de llegada programada',
  `estado` ENUM('programado','a_tiempo','retrasado','cancelado') NOT NULL COMMENT 'Estado del vuelo',
  `retraso_min` SMALLINT NOT NULL DEFAULT 0 COMMENT 'Minutos de retraso acumulados',
  PRIMARY KEY (`id`),
  KEY `origen` (`origen`),
  KEY `destino` (`destino`),
  KEY `avion_id` (`avion_id`),
  CONSTRAINT `vuelos_ibfk_1` FOREIGN KEY (`origen`) REFERENCES `aeropuertos` (`iata`),
  CONSTRAINT `vuelos_ibfk_2` FOREIGN KEY (`destino`) REFERENCES `aeropuertos` (`iata`),
  CONSTRAINT `vuelos_ibfk_3` FOREIGN KEY (`avion_id`) REFERENCES `aviones` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Vuelos programados por la aerolinea';

CREATE TABLE `pasajeros` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre completo del pasajero',
  `pasaporte` VARCHAR(20) NOT NULL COMMENT 'Numero de pasaporte',
  `nacionalidad` VARCHAR(60) NOT NULL COMMENT 'Nacionalidad del pasajero',
  `fecha_nacimiento` DATE NOT NULL COMMENT 'Fecha de nacimiento',
  `millas` INT NOT NULL DEFAULT 0 COMMENT 'Millas acumuladas en el programa de viajero frecuente',
  PRIMARY KEY (`id`),
  UNIQUE KEY `pasaporte` (`pasaporte`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Pasajeros registrados';

CREATE TABLE `reservas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `vuelo_id` INT NOT NULL COMMENT 'Vuelo reservado',
  `pasajero_id` INT NOT NULL COMMENT 'Pasajero que viaja',
  `clase` ENUM('economica','ejecutiva','primera') NOT NULL COMMENT 'Clase del boleto',
  `precio` DECIMAL(10,2) NOT NULL COMMENT 'Precio pagado en dolares',
  `fecha_reserva` DATE NOT NULL COMMENT 'Fecha en que se compro el boleto',
  `asiento` VARCHAR(4) DEFAULT NULL COMMENT 'Asiento asignado, NULL si no tiene',
  PRIMARY KEY (`id`),
  KEY `vuelo_id` (`vuelo_id`),
  KEY `pasajero_id` (`pasajero_id`),
  CONSTRAINT `reservas_ibfk_1` FOREIGN KEY (`vuelo_id`) REFERENCES `vuelos` (`id`),
  CONSTRAINT `reservas_ibfk_2` FOREIGN KEY (`pasajero_id`) REFERENCES `pasajeros` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Reservas de los pasajeros en cada vuelo';

CREATE TABLE `tripulacion` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(120) NOT NULL COMMENT 'Nombre del tripulante',
  `rol` ENUM('piloto','copiloto','sobrecargo') NOT NULL COMMENT 'Rol a bordo',
  `licencia` VARCHAR(20) NOT NULL COMMENT 'Numero de licencia aeronautica',
  `horas_vuelo` INT NOT NULL DEFAULT 0 COMMENT 'Horas de vuelo acumuladas',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Personal de tripulacion';

CREATE TABLE `vuelo_tripulacion` (
  `vuelo_id` INT NOT NULL COMMENT 'Vuelo asignado',
  `tripulante_id` INT NOT NULL COMMENT 'Tripulante asignado al vuelo',
  PRIMARY KEY (`vuelo_id`,`tripulante_id`),
  KEY `tripulante_id` (`tripulante_id`),
  CONSTRAINT `vuelo_tripulacion_ibfk_1` FOREIGN KEY (`vuelo_id`) REFERENCES `vuelos` (`id`),
  CONSTRAINT `vuelo_tripulacion_ibfk_2` FOREIGN KEY (`tripulante_id`) REFERENCES `tripulacion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Asignacion de tripulacion a cada vuelo';
