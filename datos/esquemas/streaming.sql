-- Esquema 11: streaming (ingles, nombres completos)
CREATE TABLE `genres` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(60) NOT NULL COMMENT 'Genre name',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Genres used to classify titles';

CREATE TABLE `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(120) NOT NULL COMMENT 'Account email',
  `country` VARCHAR(60) NOT NULL COMMENT 'Country of the account',
  `signup_date` DATE NOT NULL COMMENT 'Date the account was created',
  `plan` ENUM('basic','standard','premium') NOT NULL COMMENT 'Current subscription plan',
  `active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1 if the account is active',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Platform user accounts';

CREATE TABLE `titles` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(160) NOT NULL COMMENT 'Title name',
  `type` ENUM('movie','series','documentary') NOT NULL COMMENT 'Kind of content',
  `genre_id` INT NOT NULL COMMENT 'Main genre of the title',
  `release_year` SMALLINT NOT NULL COMMENT 'Year the title was released',
  `duration_min` SMALLINT DEFAULT NULL COMMENT 'Duration in minutes for movies, NULL for series',
  `rating` DECIMAL(3,1) NOT NULL COMMENT 'Average user rating from 0 to 10',
  PRIMARY KEY (`id`),
  KEY `genre_id` (`genre_id`),
  CONSTRAINT `titles_ibfk_1` FOREIGN KEY (`genre_id`) REFERENCES `genres` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Catalog of titles available on the platform';

CREATE TABLE `episodes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title_id` INT NOT NULL COMMENT 'Series the episode belongs to',
  `season` TINYINT NOT NULL COMMENT 'Season number',
  `number` SMALLINT NOT NULL COMMENT 'Episode number within the season',
  `name` VARCHAR(160) NOT NULL COMMENT 'Episode name',
  `duration_min` SMALLINT NOT NULL COMMENT 'Episode duration in minutes',
  PRIMARY KEY (`id`),
  KEY `title_id` (`title_id`),
  CONSTRAINT `episodes_ibfk_1` FOREIGN KEY (`title_id`) REFERENCES `titles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Episodes of the series in the catalog';

CREATE TABLE `views` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL COMMENT 'User who watched',
  `title_id` INT NOT NULL COMMENT 'Title watched',
  `episode_id` INT DEFAULT NULL COMMENT 'Episode watched, NULL for movies',
  `watched_at` DATETIME NOT NULL COMMENT 'Timestamp when the view started',
  `minutes_watched` SMALLINT NOT NULL COMMENT 'Minutes actually watched in the session',
  `device` ENUM('tv','mobile','web','tablet') NOT NULL COMMENT 'Device used to watch',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `title_id` (`title_id`),
  KEY `episode_id` (`episode_id`),
  CONSTRAINT `views_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `views_ibfk_2` FOREIGN KEY (`title_id`) REFERENCES `titles` (`id`),
  CONSTRAINT `views_ibfk_3` FOREIGN KEY (`episode_id`) REFERENCES `episodes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Viewing sessions logged by the platform';

CREATE TABLE `subscriptions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL COMMENT 'Subscriber',
  `start_date` DATE NOT NULL COMMENT 'First day of the billing period',
  `end_date` DATE DEFAULT NULL COMMENT 'Last day of the period, NULL if ongoing',
  `monthly_price` DECIMAL(8,2) NOT NULL COMMENT 'Price charged per month in USD',
  `status` ENUM('active','cancelled','past_due') NOT NULL COMMENT 'Status of the subscription',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `subscriptions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Subscription periods billed to users';
