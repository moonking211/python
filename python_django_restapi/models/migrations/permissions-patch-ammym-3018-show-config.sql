-- AMMYM-3018 Show Config
INSERT INTO `auth_permission` VALUES (3023, 'Can use show config tool', 50, 'tools.any.read.show_config');

UPDATE `auth_permission`
SET `codename` = 'tools.own.read.*,!resubmission,!advertiser_bidder_insight,!publisher_bidder_insight,!show_config'
WHERE `id` = 3062;

INSERT INTO `auth_group_permissions` (`group_id`,`permission_id`) VALUES
    (25, 3023),(26, 3023),(27, 3023),(28, 3023),(29, 3023),(30, 3023),(31, 3023);
