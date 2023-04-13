CREATE TABLE `recipe` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `title` varchar(255),
  `source_url` varchar(255),
  `image_url` varchar(255),
  `category` varchar(255),
  `cuisine` varchar(255),
  `instructions` text,
  `cook_time_minutes` int,
  `total_time_minutes` int,
  `yields` varchar(255),
  `created_at` datetime,
  `updated_at` datetime
);

CREATE TABLE `ingredient` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255)
);

CREATE TABLE `recipe_ingredient` (
  `recipe_id` int,
  `ingredient_id` int,
  `quantity` varchar(255),
  `unit` varchar(255)
);

CREATE TABLE `instruction` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `recipe_id` int,
  `position` int,
  `text` text
);

CREATE TABLE `nutrition` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `recipe_id` int,
  `calories` int,
  `protein` int,
  `fat` int,
  `carbohydrates` int,
  `sugar` int,
  `fiber` int,
  `cholesterol` int,
  `sodium` int
);

ALTER TABLE `recipe_ingredient` ADD FOREIGN KEY (`recipe_id`) REFERENCES `recipe` (`id`);

ALTER TABLE `recipe_ingredient` ADD FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient` (`id`);

ALTER TABLE `instruction` ADD FOREIGN KEY (`recipe_id`) REFERENCES `recipe` (`id`);

ALTER TABLE `nutrition` ADD FOREIGN KEY (`recipe_id`) REFERENCES `recipe` (`id`);
