-- Validacion 02: hotel (ingles). No aparece en el entrenamiento.
CREATE TABLE `room_types` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(60) NOT NULL COMMENT 'Room type name, for example double',
  `capacity` TINYINT NOT NULL COMMENT 'Maximum number of guests',
  `base_rate` DECIMAL(8,2) NOT NULL COMMENT 'Base nightly rate in USD',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Room categories offered by the hotel';

CREATE TABLE `rooms` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `room_number` VARCHAR(8) NOT NULL COMMENT 'Room number as shown on the door',
  `type_id` INT NOT NULL COMMENT 'Room type of this room',
  `floor` TINYINT NOT NULL COMMENT 'Floor where the room is located',
  `status` ENUM('available','occupied','maintenance') NOT NULL COMMENT 'Current room status',
  PRIMARY KEY (`id`),
  UNIQUE KEY `room_number` (`room_number`),
  KEY `type_id` (`type_id`),
  CONSTRAINT `rooms_ibfk_1` FOREIGN KEY (`type_id`) REFERENCES `room_types` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Physical rooms of the hotel';

CREATE TABLE `guests` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `full_name` VARCHAR(120) NOT NULL COMMENT 'Guest full name',
  `email` VARCHAR(120) NOT NULL COMMENT 'Guest contact email',
  `country` VARCHAR(60) NOT NULL COMMENT 'Country of origin',
  `loyalty_tier` ENUM('none','silver','gold','platinum') NOT NULL DEFAULT 'none' COMMENT 'Loyalty program tier',
  `signup_date` DATE NOT NULL COMMENT 'Date the guest profile was created',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Guests registered at the hotel';

CREATE TABLE `bookings` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `guest_id` INT NOT NULL COMMENT 'Guest who made the booking',
  `room_id` INT NOT NULL COMMENT 'Room assigned to the booking',
  `check_in` DATE NOT NULL COMMENT 'Check-in date',
  `check_out` DATE DEFAULT NULL COMMENT 'Check-out date, NULL if the stay is open',
  `nights` SMALLINT NOT NULL COMMENT 'Number of nights booked',
  `total_amount` DECIMAL(10,2) NOT NULL COMMENT 'Total charged for the stay in USD',
  `status` ENUM('confirmed','checked_in','checked_out','cancelled') NOT NULL COMMENT 'Booking status',
  `channel` ENUM('web','agency','walk_in','phone') NOT NULL COMMENT 'Channel the booking came from',
  PRIMARY KEY (`id`),
  KEY `guest_id` (`guest_id`),
  KEY `room_id` (`room_id`),
  CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`guest_id`) REFERENCES `guests` (`id`),
  CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Room bookings made by guests';

CREATE TABLE `services` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(80) NOT NULL COMMENT 'Service name, for example breakfast',
  `price` DECIMAL(8,2) NOT NULL COMMENT 'Service price in USD',
  `category` ENUM('food','spa','transport','laundry') NOT NULL COMMENT 'Service category',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Extra services the hotel sells';

CREATE TABLE `booking_services` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `booking_id` INT NOT NULL COMMENT 'Booking the service was charged to',
  `service_id` INT NOT NULL COMMENT 'Service consumed',
  `quantity` SMALLINT NOT NULL COMMENT 'Units consumed',
  `charged_at` DATE NOT NULL COMMENT 'Date the service was charged',
  PRIMARY KEY (`id`),
  KEY `booking_id` (`booking_id`),
  KEY `service_id` (`service_id`),
  CONSTRAINT `booking_services_ibfk_1` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`),
  CONSTRAINT `booking_services_ibfk_2` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Services charged to each booking';

CREATE TABLE `guest_reviews` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `booking_id` INT NOT NULL COMMENT 'Booking being reviewed',
  `score` TINYINT NOT NULL COMMENT 'Score from 1 to 5',
  `submitted_at` DATE NOT NULL COMMENT 'Date the review was submitted',
  PRIMARY KEY (`id`),
  KEY `booking_id` (`booking_id`),
  CONSTRAINT `guest_reviews_ibfk_1` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Guest reviews left after a stay';
