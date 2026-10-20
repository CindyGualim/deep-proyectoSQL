-- Esquema 08: gym (ingles, nombres abreviados)
CREATE TABLE `plan` (
  `plan_id` INT NOT NULL AUTO_INCREMENT,
  `plan_nm` VARCHAR(40) NOT NULL COMMENT 'Membership plan name',
  `fee` DECIMAL(8,2) NOT NULL COMMENT 'Monthly fee in USD',
  `max_cls` TINYINT NOT NULL COMMENT 'Maximum classes per month allowed by the plan',
  PRIMARY KEY (`plan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Membership plans offered by the gym';

CREATE TABLE `mbr` (
  `mbr_id` INT NOT NULL AUTO_INCREMENT,
  `fname` VARCHAR(60) NOT NULL COMMENT 'Member first name',
  `lname` VARCHAR(60) NOT NULL COMMENT 'Member last name',
  `email` VARCHAR(120) NOT NULL COMMENT 'Member email',
  `birth_dt` DATE NOT NULL COMMENT 'Date of birth',
  `join_dt` DATE NOT NULL COMMENT 'Date the member joined the gym',
  `status` ENUM('active','frozen','cancelled') NOT NULL COMMENT 'Membership status',
  PRIMARY KEY (`mbr_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Gym members';

CREATE TABLE `mbrship` (
  `ms_id` INT NOT NULL AUTO_INCREMENT,
  `mbr_id` INT NOT NULL COMMENT 'Member holding the membership',
  `plan_id` INT NOT NULL COMMENT 'Plan contracted',
  `start_dt` DATE NOT NULL COMMENT 'Start date of the membership period',
  `end_dt` DATE DEFAULT NULL COMMENT 'End date, NULL if still running',
  `paid` DECIMAL(8,2) NOT NULL COMMENT 'Amount paid for the period in USD',
  PRIMARY KEY (`ms_id`),
  KEY `mbr_id` (`mbr_id`),
  KEY `plan_id` (`plan_id`),
  CONSTRAINT `mbrship_ibfk_1` FOREIGN KEY (`mbr_id`) REFERENCES `mbr` (`mbr_id`),
  CONSTRAINT `mbrship_ibfk_2` FOREIGN KEY (`plan_id`) REFERENCES `plan` (`plan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Membership periods contracted by members';

CREATE TABLE `trn` (
  `trn_id` INT NOT NULL AUTO_INCREMENT,
  `trn_nm` VARCHAR(80) NOT NULL COMMENT 'Trainer full name',
  `specialty` VARCHAR(60) NOT NULL COMMENT 'Training specialty',
  `rate` DECIMAL(8,2) NOT NULL COMMENT 'Hourly rate in USD',
  `hire_dt` DATE NOT NULL COMMENT 'Date the trainer was hired',
  PRIMARY KEY (`trn_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Trainers working at the gym';

CREATE TABLE `cls` (
  `cls_id` INT NOT NULL AUTO_INCREMENT,
  `cls_nm` VARCHAR(60) NOT NULL COMMENT 'Class name, for example spinning',
  `trn_id` INT NOT NULL COMMENT 'Trainer who leads the class',
  `cap` TINYINT NOT NULL COMMENT 'Maximum number of attendees',
  `dur_min` SMALLINT NOT NULL COMMENT 'Duration in minutes',
  `room` VARCHAR(20) NOT NULL COMMENT 'Room where the class takes place',
  PRIMARY KEY (`cls_id`),
  KEY `trn_id` (`trn_id`),
  CONSTRAINT `cls_ibfk_1` FOREIGN KEY (`trn_id`) REFERENCES `trn` (`trn_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Classes scheduled at the gym';

CREATE TABLE `bkg` (
  `bkg_id` INT NOT NULL AUTO_INCREMENT,
  `cls_id` INT NOT NULL COMMENT 'Class booked',
  `mbr_id` INT NOT NULL COMMENT 'Member who booked',
  `bkg_dt` DATETIME NOT NULL COMMENT 'Date and time of the booked session',
  `attended` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 if the member showed up',
  PRIMARY KEY (`bkg_id`),
  KEY `cls_id` (`cls_id`),
  KEY `mbr_id` (`mbr_id`),
  CONSTRAINT `bkg_ibfk_1` FOREIGN KEY (`cls_id`) REFERENCES `cls` (`cls_id`),
  CONSTRAINT `bkg_ibfk_2` FOREIGN KEY (`mbr_id`) REFERENCES `mbr` (`mbr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Class bookings made by members';
