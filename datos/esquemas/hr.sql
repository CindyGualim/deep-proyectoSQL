-- Esquema 05: hr (ingles, recursos humanos)
CREATE TABLE `departments` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(80) NOT NULL COMMENT 'Department name',
  `location` VARCHAR(80) NOT NULL COMMENT 'Office location of the department',
  `budget` DECIMAL(12,2) NOT NULL COMMENT 'Annual budget in USD',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Company departments';

CREATE TABLE `positions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(80) NOT NULL COMMENT 'Job title',
  `level` ENUM('junior','mid','senior','lead') NOT NULL COMMENT 'Seniority level',
  `min_salary` DECIMAL(10,2) NOT NULL COMMENT 'Minimum salary of the band',
  `max_salary` DECIMAL(10,2) NOT NULL COMMENT 'Maximum salary of the band',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Job positions and their salary bands';

CREATE TABLE `employees` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(60) NOT NULL COMMENT 'Employee first name',
  `last_name` VARCHAR(60) NOT NULL COMMENT 'Employee last name',
  `email` VARCHAR(120) NOT NULL COMMENT 'Corporate email',
  `department_id` INT NOT NULL COMMENT 'Department the employee works in',
  `position_id` INT NOT NULL COMMENT 'Position held by the employee',
  `manager_id` INT DEFAULT NULL COMMENT 'Direct manager, NULL for top level',
  `hire_date` DATE NOT NULL COMMENT 'Date the employee was hired',
  `salary` DECIMAL(10,2) NOT NULL COMMENT 'Current monthly salary in USD',
  `active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1 if the employee still works here',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `department_id` (`department_id`),
  KEY `position_id` (`position_id`),
  KEY `manager_id` (`manager_id`),
  CONSTRAINT `employees_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`),
  CONSTRAINT `employees_ibfk_2` FOREIGN KEY (`position_id`) REFERENCES `positions` (`id`),
  CONSTRAINT `employees_ibfk_3` FOREIGN KEY (`manager_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Employees of the company';

CREATE TABLE `attendance` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `employee_id` INT NOT NULL COMMENT 'Employee the record belongs to',
  `work_date` DATE NOT NULL COMMENT 'Date of the attendance record',
  `hours_worked` DECIMAL(4,2) NOT NULL COMMENT 'Hours worked that day',
  `status` ENUM('present','remote','absent','vacation') NOT NULL COMMENT 'Attendance status',
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Daily attendance records';

CREATE TABLE `payroll` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `employee_id` INT NOT NULL COMMENT 'Employee being paid',
  `period` VARCHAR(7) NOT NULL COMMENT 'Payroll period in YYYY-MM format',
  `gross` DECIMAL(10,2) NOT NULL COMMENT 'Gross pay in USD',
  `deductions` DECIMAL(10,2) NOT NULL COMMENT 'Total deductions in USD',
  `net` DECIMAL(10,2) NOT NULL COMMENT 'Net pay in USD',
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `payroll_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Monthly payroll per employee';

CREATE TABLE `trainings` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(120) NOT NULL COMMENT 'Training course name',
  `provider` VARCHAR(80) NOT NULL COMMENT 'Company that delivers the training',
  `hours` SMALLINT NOT NULL COMMENT 'Duration in hours',
  `cost` DECIMAL(8,2) NOT NULL COMMENT 'Cost per seat in USD',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Training courses offered to employees';

CREATE TABLE `employee_trainings` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `employee_id` INT NOT NULL COMMENT 'Employee enrolled',
  `training_id` INT NOT NULL COMMENT 'Training taken',
  `completed_at` DATE DEFAULT NULL COMMENT 'Completion date, NULL if not finished',
  `score` DECIMAL(5,2) DEFAULT NULL COMMENT 'Final score from 0 to 100',
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  KEY `training_id` (`training_id`),
  CONSTRAINT `employee_trainings_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `employee_trainings_ibfk_2` FOREIGN KEY (`training_id`) REFERENCES `trainings` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Trainings taken by each employee';
