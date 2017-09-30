ALTER TABLE `auth_user` MODIFY `last_login` DATETIME;

INSERT INTO `django_content_type` VALUES (50, 'tools', 'restapi', 'tools');

DELETE FROM `auth_permission` WHERE `id` IN (1315,1313,1361,1362,1363,1405,1411,1413,1415,1425,1461,1462,1463,1465,1475,1561,1562,1563,1571,1575,1576,3002,3012,3052,3062);
INSERT INTO `auth_permission` VALUES
    (1315, 'Can do any action on Campaign',         54, 'campaign.any.action.*,!targeting_json_update'),
    (1313, 'Can update any Campaign record',        54, 'campaign.any.update.*,!targeting'),
    (1361, 'Can create own Campaign record*',       54, 'campaign.own.create.*,!targeting,!total_cost_cap,!daily_cost_cap,!daily_loss_cap,!total_loss_cap,!priority'),
    (1362, 'Can read own Campaign record*',         54, 'campaign.own.read.*,!total_cost_cap,!daily_cost_cap,!daily_loss_cap,!total_loss_cap,!priority,!targeting.min_slice,!targeting.max_slice'),
    (1363, 'Can update own Campaign record*',       54, 'campaign.own.update.*,!total_cost_cap,!daily_cost_cap,!daily_loss_cap,!total_loss_cap,!priority,!targeting.min_slice,!targeting.max_slice'),
    (1405, 'Can do any action on any AdGroup',      55, 'adgroup.any.action.*'),
    (1411, 'Can create any AdGroup record',         55, 'adgroup.any.create.*,!priority'),
    (1413, 'Can update any AdGroup record',         55, 'adgroup.any.update.*,!priority'),
    (1415, 'Can do any action on any AdGroup*',     55, 'adgroup.any.action.*,!bulk,!import,!targeting_json_update'),
    (1425, 'Can do any action on any AdGroup*',     55, 'adgroup.any.action.*,!targeting_json_update'),
    (1461, 'Can create own AdGroup record*',        55, 'adgroup.own.create.*,!targeting,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority'),
    (1462, 'Can read own AdGroup record*',          55, 'adgroup.own.read.*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_rev_type,!revmap_rev_value,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice'),
    (1463, 'Can update own AdGroup record*',        55, 'adgroup.own.update.*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_rev_type,!revmap_rev_value,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice'),
    (1465, 'Can do any action on own AdGroup*',     55, 'adgroup.own.action.*,!bulk,!import,!rates,!limits,!targeting_json_read,!targeting_json_update'),
    (1475, 'Can do any action on own AdGroup*',     55, 'adgroup.own.action.*,!rates,!limits,!targeting_json_read,!targeting_json_update'),
    (1561, 'Can create own Ad record',              56, 'ad.own.create.*,!external_args'),
    (1562, 'Can read own Ad record',                56, 'ad.own.read.*,!html,!external_args'),
    (1563, 'Can update own Ad record',              56, 'ad.own.update.*,!external_args'),
    (1571, 'Can do any action on any Ad*',          56, 'ad.any.action.*,!bulk_re_submit_to_adx,!bulk'),
    (1575, 'Can do any action on own Ad*',          56, 'ad.own.action.*,!bulk_re_submit_to_adx,!bulk'),
    (1576, 'Can do any action on own Ad*',          56, 'ad.own.action.*,!bulk_re_submit_to_adx'),
    (3002, 'Can use any tool',                      50, 'tools.any.read.*'),
    (3012, 'Can use any tool',                      50, 'tools.any.read.*,!resubmission'),
    (3052, 'Can use own tool',                      50, 'tools.own.read.*'),
    (3062, 'Can use own tool',                      50, 'tools.own.read.*,!resubmission,!advertiser_bidder_insight,!publisher_bidder_insight');
 
DELETE FROM `auth_group_permissions` WHERE
       (`permission_id` = 1013 AND `group_id` IN (25,27,28,29,30))
    OR (`permission_id` = 1351 AND `group_id` IN (22,23,24))
    OR (`permission_id` = 1352 AND `group_id` IN (22,23,24))
    OR (`permission_id` = 1353 AND `group_id` IN (22,23,24));
INSERT IGNORE INTO `auth_group_permissions` (group_id, permission_id) VALUES
    (22, 1361), (22, 1362), (22, 1363), (23, 1361), (23, 1362), (23, 1363), (24, 1361), (24, 1362), (24, 1363), (25, 1315),
    (26, 1305), (27, 1315), (28, 1315), (29, 1315), (30, 1313), (30, 1315), (31, 1313), (31, 1315), (25, 1402), (25, 1415),
    (26, 1401), (26, 1402), (26, 1403), (26, 1405), (27, 1411), (27, 1402), (27, 1413), (27, 1425), (28, 1411), (28, 1402),
    (28, 1413), (28, 1425), (29, 1411), (29, 1402), (29, 1413), (29, 1425), (30, 1402), (30, 1415), (31, 1402), (31, 1415),
    (21, 1462), (21, 1465), (22, 1461), (22, 1462), (22, 1463), (22, 1475), (23, 1461), (23, 1462), (23, 1463), (23, 1475),
    (24, 1461), (24, 1462), (24, 1463), (24, 1475), (25, 1502), (25, 1571), (26, 1501), (26, 1502), (26, 1503), (27, 1501),
    (27, 1502), (27, 1503), (28, 1501), (28, 1502), (28, 1503), (29, 1501), (29, 1502), (29, 1503), (30, 1502), (30, 1571),
    (31, 1502), (31, 1571), (21, 1562), (21, 1575), (22, 1551), (22, 1562), (22, 1553), (22, 1576), (23, 1551), (23, 1562),
    (23, 1553), (23, 1576), (24, 1551), (24, 1562), (24, 1553), (24, 1576), (25, 1702), (26, 1702), (27, 1702), (28, 1702),
    (29, 1702), (30, 1702), (31, 1702), (21, 1752), (22, 1752), (23, 1752), (24, 1752), (26, 1804), (27, 1804), (28, 1804),
    (29, 1804), (22, 1854), (23, 1854), (24, 1854), (26, 1904), (27, 1904), (28, 1904), (29, 1904), (22, 1954), (23, 1954),
    (24, 1954), (26, 2004), (27, 2004), (28, 2004), (29, 2004), (22, 2054), (23, 2054), (24, 2054), (26, 3002), (27, 3002),
    (28, 3002), (29, 3002), (30, 3002), (31, 3002), (22, 3062), (23, 3062), (24, 3062), (25, 3012);
