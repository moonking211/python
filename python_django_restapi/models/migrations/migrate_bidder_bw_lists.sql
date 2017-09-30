ALTER TABLE `bidder_blacklist` ADD `id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT FIRST;
ALTER TABLE `bidder_whitelist` ADD `id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT FIRST;

ALTER TABLE `custom_hint`
    DROP PRIMARY KEY,
    ADD UNIQUE KEY(`campaign_id`,`ad_group_id`,`ad_id`,`source_id`,`size`,`placement_type`,`placement_id`),
    ADD `id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT FIRST;

