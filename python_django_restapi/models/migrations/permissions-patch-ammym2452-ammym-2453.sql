-- AMMYM-2452 Campaign: Manage Account Manager and Manage TD Account Manager can change status and edit Campaign
DELETE FROM `auth_group_permissions` WHERE (`permission_id` = 1313 AND `group_id` IN (30, 31));

-- AMMYM-2453 Campaign: Manage AD Ops head, Manage Ad Ops and Manage Analyst can edit priority of the Campaign
INSERT INTO `auth_permission` VALUES (1323, 'Can update any Campaign record', 54, 'campaign.any.update.*,!priority');
UPDATE `auth_group_permissions` SET `permission_id` = 1323 WHERE (`permission_id` = 1303 AND `group_id` IN (27, 28, 29));
