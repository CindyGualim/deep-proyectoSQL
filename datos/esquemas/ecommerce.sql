-- Esquema 02: ecommerce (ingles, nombres completos)
CREATE TABLE `categories` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(80) NOT NULL COMMENT 'Category name',
  `parent_id` INT DEFAULT NULL COMMENT 'Parent category, NULL for top level',
  PRIMARY KEY (`id`),
  KEY `parent_id` (`parent_id`),
  CONSTRAINT `categories_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Product category tree';

CREATE TABLE `products` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(160) NOT NULL COMMENT 'Product display name',
  `sku` VARCHAR(24) NOT NULL COMMENT 'Stock keeping unit',
  `category_id` INT NOT NULL COMMENT 'Category the product belongs to',
  `price` DECIMAL(10,2) NOT NULL COMMENT 'Unit list price in USD',
  `cost` DECIMAL(10,2) NOT NULL COMMENT 'Unit cost in USD',
  `stock` INT NOT NULL DEFAULT 0 COMMENT 'Units available in warehouse',
  `active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1 if the product is for sale',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `products_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Products in the online catalog';

CREATE TABLE `customers` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `full_name` VARCHAR(120) NOT NULL COMMENT 'Customer full name',
  `email` VARCHAR(120) NOT NULL COMMENT 'Contact email',
  `country` VARCHAR(60) NOT NULL COMMENT 'Country of residence',
  `city` VARCHAR(60) NOT NULL COMMENT 'City of residence',
  `signup_date` DATE NOT NULL COMMENT 'Date the account was created',
  `segment` ENUM('new','regular','vip') NOT NULL DEFAULT 'new' COMMENT 'Loyalty segment',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Registered customers';

CREATE TABLE `orders` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `customer_id` INT NOT NULL COMMENT 'Customer who placed the order',
  `order_date` DATETIME NOT NULL COMMENT 'Timestamp when the order was placed',
  `status` ENUM('pending','paid','shipped','delivered','cancelled') NOT NULL COMMENT 'Current order status',
  `shipping_cost` DECIMAL(8,2) NOT NULL DEFAULT 0.00 COMMENT 'Shipping charged in USD',
  `channel` ENUM('web','app','phone') NOT NULL DEFAULT 'web' COMMENT 'Sales channel used',
  PRIMARY KEY (`id`),
  KEY `customer_id` (`customer_id`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Orders placed by customers';

CREATE TABLE `order_items` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `order_id` INT NOT NULL COMMENT 'Parent order',
  `product_id` INT NOT NULL COMMENT 'Product sold in this line',
  `quantity` SMALLINT NOT NULL COMMENT 'Units sold in this line',
  `unit_price` DECIMAL(10,2) NOT NULL COMMENT 'Price charged per unit',
  `discount` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT 'Discount percentage applied to the line',
  PRIMARY KEY (`id`),
  KEY `order_id` (`order_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Line items of each order';

CREATE TABLE `payments` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `order_id` INT NOT NULL COMMENT 'Order being paid',
  `method` ENUM('card','paypal','transfer','cash') NOT NULL COMMENT 'Payment method',
  `amount` DECIMAL(10,2) NOT NULL COMMENT 'Amount paid in USD',
  `paid_at` DATETIME NOT NULL COMMENT 'Timestamp of the payment',
  PRIMARY KEY (`id`),
  KEY `order_id` (`order_id`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Payments received for orders';

CREATE TABLE `reviews` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `product_id` INT NOT NULL COMMENT 'Reviewed product',
  `customer_id` INT NOT NULL COMMENT 'Customer who wrote the review',
  `rating` TINYINT NOT NULL COMMENT 'Score from 1 to 5',
  `created_at` DATE NOT NULL COMMENT 'Date the review was posted',
  PRIMARY KEY (`id`),
  KEY `product_id` (`product_id`),
  KEY `customer_id` (`customer_id`),
  CONSTRAINT `reviews_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `reviews_ibfk_2` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Product reviews written by customers';
