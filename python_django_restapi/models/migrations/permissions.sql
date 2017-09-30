ALTER TABLE `auth_user` MODIFY `last_login` DATETIME;

-- Add `userprofile_id` and `tradingdesk_id` keys ------------------------------
DROP TABLE IF EXISTS `userprofile_trading_desks`;
CREATE TABLE `userprofile_trading_desks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `userprofile_id` int(11) NOT NULL,
  `tradingdesk_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `userprofile_id` (`userprofile_id`,`tradingdesk_id`),
  KEY (`userprofile_id`),
  KEY (`tradingdesk_id`)
) ENGINE=MyISAM;

-- Permissions cleanup ---------------------------------------------------------
DELETE FROM `auth_user_user_permissions` WHERE `permission_id` IN (
    SELECT `id` FROM `auth_permission` WHERE `content_type_id` IN (
        SELECT `id` FROM `django_content_type` WHERE `app_label`='restapi'));
DELETE FROM `auth_group_permissions` WHERE `group_id` in (21,22,23,24,25,26,27,28,29,30,31,32,33,34);
DELETE FROM `auth_group` WHERE `id` IN (21,22,23,24,25,26,27,28,29,30,31,32,33,34);
DELETE FROM `auth_permission` WHERE `content_type_id` IN (
    SELECT `id` FROM `django_content_type` WHERE `app_label`='restapi'
);
DELETE FROM `django_content_type` WHERE `app_label`='restapi';

-- Permissions setup -----------------------------------------------------------
ALTER TABLE `auth_permission` MODIFY `codename` VARCHAR(996) NOT NULL;
INSERT INTO `django_content_type` VALUES
    (50, 'tools',               'restapi', 'tools'),
    (51, 'trading_desk',        'restapi', 'trading_desk'),
    (52, 'agency',              'restapi', 'agency'),
    (53, 'advertiser',          'restapi', 'advertiser'),
    (54, 'campaign',            'restapi', 'campaign'),
    (55, 'ad_group',            'restapi', 'ad_group'),
    (56, 'ad',                  'restapi', 'ad'),
    (57, 'app',                 'restapi', 'app'),
    (58, 'audit_log',           'restapi', 'audit_log'),
    (59, 'bidder_black_list',   'restapi', 'bidder_black_list'),
    (60, 'bidder_white_list',   'restapi', 'bidder_white_list'),
    (61, 'custom_hint',         'restapi', 'custom_hint'),
    (62, 'event',               'restapi', 'event'),
    (63, 'manage_user',         'restapi', 'manage_user'),
    (64, 'publisher',           'restapi', 'publisher'),
    (65, 'revmap',              'restapi', 'revmap'),
    (66, 'role',                'restapi', 'role'),
    (67, 'source',              'restapi', 'source'),
    (68, 'userprofile',         'restapi', 'userprofile'),
    (69, 'user',                'restapi', 'user'),
    (70, 'zone',                'restapi', 'zone');

INSERT INTO `auth_permission` VALUES
    (1001, 'Can create any Trading Desk record',    51, 'tradingdesk.any.create.*'),
    (1002, 'Can read any Trading Desk record',      51, 'tradingdesk.any.read.*'),
    (1003, 'Can update any Trading Desk record',    51, 'tradingdesk.any.update.*'),
    (1004, 'Can delete any Trading Desk record',    51, 'tradingdesk.any.delete.*'),
    (1005, 'Can do any action on Trading Desk',     51, 'tradingdesk.any.action.*'),
    (1013, 'Can update status of any Trading Desk', 51, 'tradingdesk.any.update.status'),
    (1023, 'Can update any Trading Desk record*',   51, 'tradingdesk.any.update.*,!currency'),
    (1051, 'Can create own Trading Desk record',    51, 'tradingdesk.own.create.*'),
    (1052, 'Can read own Trading Desk record',      51, 'tradingdesk.own.read.*'),
    (1053, 'Can update own Trading Desk record',    51, 'tradingdesk.own.update.*'),
    (1054, 'Can delete own Trading Desk record',    51, 'tradingdesk.own.delete.*'),
    (1055, 'Can do any action Trading Desk',        51, 'tradingdesk.own.action.*'),
    (1062, 'Can read own Trading Desk record',      51, 'tradingdesk.own.read.trading_desk_id,trading_desk'),

    (1101, 'Can create any Agency record',          52, 'agency.any.create.*'),
    (1102, 'Can read any Agency record',            52, 'agency.any.read.*'),
    (1103, 'Can update any Agency record',          52, 'agency.any.update.*'),
    (1104, 'Can delete any Agency record',          52, 'agency.any.delete.*'),
    (1105, 'Can do any action on Agency',           52, 'agency.any.action.*'),
    (1113, 'Can update any Agency record*',         52, 'agency.any.update.*,!currency,!agency_key'),
    (1115, 'Can use a filter by Trading desk',      52, 'agency.any.action.filter_by_trading_desk'),
    (1151, 'Can create own Agency record',          52, 'agency.own.create.*'),
    (1152, 'Can read own Agency record',            52, 'agency.own.read.*'),
    (1153, 'Can update own Agency record',          52, 'agency.own.update.*'),
    (1154, 'Can delete own Agency record',          52, 'agency.own.delete.*'),
    (1155, 'Can do any action on Agency',           52, 'agency.own.action.*'),
    (1161, 'Can create own Agency record*',         52, 'agency.own.create.*,!trading_desk_id,!currency,!agency_key'),
    (1162, 'Can read own Agency record*',           52, 'agency.own.read.*,!currency,!agency_key'),
    (1163, 'Can update own Agency record*',         52, 'agency.own.update.*,!trading_desk_id,!currency,!agency_key'),

    (1201, 'Can create any Advertiser record',      53, 'advertiser.any.create.*'),
    (1202, 'Can read any Advertiser record',        53, 'advertiser.any.read.*'),
    (1203, 'Can update any Advertiser record',      53, 'advertiser.any.update.*'),
    (1204, 'Can delete any Advertiser record',      53, 'advertiser.any.delete.*'),
    (1205, 'Can do any action on Advertiser',       53, 'advertiser.any.action.*'),
    (1213, 'Can update any Advertiser record',      53, 'advertiser.any.update.*,!agency_id,!currency'),
    (1251, 'Can create own Advertiser record',      53, 'advertiser.own.create.*'),
    (1252, 'Can read own Advertiser record',        53, 'advertiser.own.read.*'),
    (1253, 'Can update own Advertiser record',      53, 'advertiser.own.update.*'),
    (1254, 'Can delete own Advertiser record',      53, 'advertiser.own.delete.*'),
    (1255, 'Can do any action on Advertiser',       53, 'advertiser.own.action.*'),
    (1261, 'Can create own Advertiser record',      53, 'advertiser.own.create.*,!advertiser_key,!currency'),
    (1262, 'Can read own Advertiser record',        53, 'advertiser.own.read.*,!advertiser_key,!currency'),
    (1263, 'Can update own Advertiser record',      53, 'advertiser.own.update.*,!advertiser_key,!currency,!agency_id'),

    (1301, 'Can create any Campaign record',        54, 'campaign.any.create.*'),
    (1302, 'Can read any Campaign record',          54, 'campaign.any.read.*'),
    (1303, 'Can update any Campaign record',        54, 'campaign.any.update.*'),
    (1304, 'Can delete any Campaign record',        54, 'campaign.any.delete.*'),
    (1305, 'Can do any action on Campaign',         54, 'campaign.any.action.*'),
    (1315, 'Can do any action on Campaign',         54, 'campaign.any.action.*,!targeting_json_update'),
    (1313, 'Can update any Campaign record',        54, 'campaign.any.update.*,!targeting'),
    (1323, 'Can update any Campaign record',        54, 'campaign.any.update.*,!priority'),
    (1351, 'Can create own Campaign record',        54, 'campaign.own.create.*'),
    (1352, 'Can read own Campaign record',          54, 'campaign.own.read.*'),
    (1353, 'Can update own Campaign record',        54, 'campaign.own.update.*'),
    (1354, 'Can delete own Campaign record',        54, 'campaign.own.delete.*'),
    (1355, 'Can do any action on Campaign',         54, 'campaign.own.action.*'),
    (1361, 'Can create own Campaign record*',       54, 'campaign.own.create.*,!targeting,!total_cost_cap,!daily_cost_cap,!daily_loss_cap,!total_loss_cap,!priority'),
    (1362, 'Can read own Campaign record*',         54, 'campaign.own.read.*,!total_cost_cap,!daily_cost_cap,!daily_loss_cap,!total_loss_cap,!priority,!targeting.min_slice,!targeting.max_slice'),
    (1363, 'Can update own Campaign record*',       54, 'campaign.own.update.*,!total_cost_cap,!daily_cost_cap,!daily_loss_cap,!total_loss_cap,!priority,!targeting.min_slice,!targeting.max_slice'),

    (1401, 'Can create any AdGroup record',         55, 'adgroup.any.create.*'),
    (1402, 'Can read any AdGroup record',           55, 'adgroup.any.read.*'),
    (1403, 'Can update any AdGroup record',         55, 'adgroup.any.update.*'),
    (1404, 'Can delete any AdGroup record',         55, 'adgroup.any.delete.*'),
    (1405, 'Can do any action on any AdGroup',      55, 'adgroup.any.action.*'),
    (1411, 'Can create any AdGroup record',         55, 'adgroup.any.create.*,!priority'),
    (1413, 'Can update any AdGroup record',         55, 'adgroup.any.update.*,!priority'),
    (1415, 'Can do any action on any AdGroup*',     55, 'adgroup.any.action.*,!bulk,!import,!targeting_json_update'),
    (1425, 'Can do any action on any AdGroup*',     55, 'adgroup.any.action.*,!targeting_json_update'),
    (1451, 'Can create own AdGroup record',         55, 'adgroup.own.create.*'),
    (1452, 'Can read own AdGroup record',           55, 'adgroup.own.read.*'),
    (1453, 'Can update own AdGroup record',         55, 'adgroup.own.update.*'),
    (1454, 'Can delete own AdGroup record',         55, 'adgroup.own.delete.*'),
    (1461, 'Can create own AdGroup record*',        55, 'adgroup.own.create.*,!targeting,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority'),
    (1462, 'Can read own AdGroup record*',          55, 'adgroup.own.read.*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_rev_type,!revmap_rev_value,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice'),
    (1463, 'Can update own AdGroup record*',        55, 'adgroup.own.update.*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_rev_type,!revmap_rev_value,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice'),
    (1465, 'Can do any action on own AdGroup*',     55, 'adgroup.own.action.*,!bulk,!import,!rates,!limits,!targeting_json_read,!targeting_json_update'),
    (1472, 'Can read own AdGroup record*',          55, 'adgroup.own.read.*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice'),
    (1473, 'Can update own AdGroup record*',        55, 'adgroup.own.update.*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice'),
    (1475, 'Can do any action on own AdGroup*',     55, 'adgroup.own.action.*,!rates,!limits,!targeting_json_read,!targeting_json_update'),

    (1501, 'Can create any Ad record',              56, 'ad.any.create.*'),
    (1502, 'Can read any Ad record',                56, 'ad.any.read.*'),
    (1503, 'Can update any Ad record',              56, 'ad.any.update.*'),
    (1504, 'Can delete any Ad record',              56, 'ad.any.delete.*'),
    (1551, 'Can create own Ad record',              56, 'ad.own.create.*'),
    (1552, 'Can read own Ad record',                56, 'ad.own.read.*'),
    (1553, 'Can update own Ad record',              56, 'ad.own.update.*'),
    (1554, 'Can delete own Ad record',              56, 'ad.own.delete.*'),
    (1561, 'Can create own Ad record',              56, 'ad.own.create.*,!external_args'),
    (1562, 'Can read own Ad record',                56, 'ad.own.read.*,!html,!external_args'),
    (1563, 'Can update own Ad record',              56, 'ad.own.update.*,!external_args'),
    (1571, 'Can do any action on any Ad*',          56, 'ad.any.action.*,!bulk_re_submit_to_adx,!bulk'),
    (1575, 'Can do any action on own Ad*',          56, 'ad.own.action.*,!bulk_re_submit_to_adx,!bulk'),
    (1576, 'Can do any action on own Ad*',          56, 'ad.own.action.*,!bulk_re_submit_to_adx'),

    (1601, 'Can create any App record',             57, 'app.any.create.*'),
    (1602, 'Can read any App record',               57, 'app.any.read.*'),
    (1603, 'Can update any App record',             57, 'app.any.update.*'),
    (1604, 'Can delete any App record',             57, 'app.any.delete.*'),
    (1651, 'Can create own App record',             57, 'app.own.create.*'),
    (1652, 'Can read own App record',               57, 'app.own.read.*'),
    (1653, 'Can update own App record',             57, 'app.own.update.*'),
    (1654, 'Can delete own App record',             57, 'app.own.delete.*'),

    (1701, 'Can create any AuditLog record',        58, 'auditlog.any.create.*'),
    (1702, 'Can read any AuditLog record',          58, 'auditlog.any.read.*'),
    (1703, 'Can update any AuditLog record',        58, 'auditlog.any.update.*'),
    (1704, 'Can delete any AuditLog record',        58, 'auditlog.any.delete.*'),
    (1751, 'Can create own AuditLog record',        58, 'auditlog.own.create.*'),
    (1752, 'Can read own AuditLog record',          58, 'auditlog.own.read.*'),
    (1753, 'Can update own AuditLog record',        58, 'auditlog.own.update.*'),
    (1754, 'Can delete own AuditLog record',        58, 'auditlog.own.delete.*'),

    (1801, 'Can create any BidderBlacklist record', 59, 'bidderblacklist.any.create.*'),
    (1802, 'Can read any BidderBlacklist record',   59, 'bidderblacklist.any.read.*'),
    (1803, 'Can update any BidderBlacklist record', 59, 'bidderblacklist.any.update.*'),
    (1804, 'Can delete any BidderBlacklist record', 59, 'bidderblacklist.any.delete.*'),
    (1851, 'Can create own BidderBlacklist record', 59, 'bidderblacklist.own.create.*'),
    (1852, 'Can read own BidderBlacklist record',   59, 'bidderblacklist.own.read.*'),
    (1853, 'Can update own BidderBlacklist record', 59, 'bidderblacklist.own.update.*'),
    (1854, 'Can delete own BidderBlacklist record', 59, 'bidderblacklist.own.delete.*'),

    (1901, 'Can create any BidderWhitelist record', 60, 'bidderwhitelist.any.create.*'),
    (1902, 'Can read any BidderWhitelist record',   60, 'bidderwhitelist.any.read.*'),
    (1903, 'Can update any BidderWhitelist record', 60, 'bidderwhitelist.any.update.*'),
    (1904, 'Can delete any BidderWhitelist record', 60, 'bidderwhitelist.any.delete.*'),
    (1951, 'Can create own BidderWhitelist record', 60, 'bidderwhitelist.own.create.*'),
    (1952, 'Can read own BidderWhitelist record',   60, 'bidderwhitelist.own.read.*'),
    (1953, 'Can update own BidderWhitelist record', 60, 'bidderwhitelist.own.update.*'),
    (1954, 'Can delete own BidderWhitelist record', 60, 'bidderwhitelist.own.delete.*'),

    (2001, 'Can create any CustomHint record',      61, 'customhint.any.create.*'),
    (2002, 'Can read any CustomHint record',        61, 'customhint.any.read.*'),
    (2003, 'Can update any CustomHint record',      61, 'customhint.any.update.*'),
    (2004, 'Can delete any CustomHint record',      61, 'customhint.any.delete.*'),
    (2051, 'Can create own CustomHint record',      61, 'customhint.own.create.*'),
    (2052, 'Can read own CustomHint record',        61, 'customhint.own.read.*'),
    (2053, 'Can update own CustomHint record',      61, 'customhint.own.update.*'),
    (2054, 'Can delete own CustomHint record',      61, 'customhint.own.delete.*'),

    (2101, 'Can create any Event record',           62, 'event.any.create.*'),
    (2102, 'Can read any Event record',             62, 'event.any.read.*'),
    (2103, 'Can update any Event record',           62, 'event.any.update.*'),
    (2104, 'Can delete any Event record',           62, 'event.any.delete.*'),
    (2151, 'Can create own Event record',           62, 'event.own.create.*'),
    (2152, 'Can read own Event record',             62, 'event.own.read.*'),
    (2153, 'Can update own Event record',           62, 'event.own.update.*'),
    (2154, 'Can delete own Event record',           62, 'event.own.delete.*'),

    (2201, 'Can create any ManageUser record',      63, 'user.any.create.*'),
    (2202, 'Can read any ManageUser record',        63, 'user.any.read.*'),
    (2203, 'Can update any ManageUser record',      63, 'user.any.update.*'),
    (2204, 'Can delete any ManageUser record',      63, 'user.any.delete.*'),
    (2251, 'Can create own ManageUser record',      63, 'user.own.create.*'),
    (2252, 'Can read own ManageUser record',        63, 'user.own.read.*'),
    (2253, 'Can update own ManageUser record',      63, 'user.own.update.*'),
    (2254, 'Can delete own ManageUser record',      63, 'user.own.delete.*'),

    (2301, 'Can create any Publisher record',       64, 'publisher.any.create.*'),
    (2302, 'Can read any Publisher record',         64, 'publisher.any.read.*'),
    (2303, 'Can update any Publisher record',       64, 'publisher.any.update.*'),
    (2304, 'Can delete any Publisher record',       64, 'publisher.any.delete.*'),
    (2351, 'Can create own Publisher record',       64, 'publisher.own.create.*'),
    (2352, 'Can read own Publisher record',         64, 'publisher.own.read.*'),
    (2353, 'Can update own Publisher record',       64, 'publisher.own.update.*'),
    (2354, 'Can delete own Publisher record',       64, 'publisher.own.delete.*'),

    (2401, 'Can create any Revmap record',          65, 'revmap.any.create.*'),
    (2402, 'Can read any Revmap record',            65, 'revmap.any.read.*'),
    (2403, 'Can update any Revmap record',          65, 'revmap.any.update.*'),
    (2404, 'Can delete any Revmap record',          65, 'revmap.any.delete.*'),
    (2451, 'Can create own Revmap record',          65, 'revmap.own.create.*'),
    (2452, 'Can read own Revmap record',            65, 'revmap.own.read.*'),
    (2453, 'Can update own Revmap record',          65, 'revmap.own.update.*'),
    (2454, 'Can delete own Revmap record',          65, 'revmap.own.delete.*'),

    (2501, 'Can create any Role record',            66, 'role.any.create.*'),
    (2502, 'Can read any Role record',              66, 'role.any.read.*'),
    (2503, 'Can update any Role record',            66, 'role.any.update.*'),
    (2504, 'Can delete any Role record',            66, 'role.any.delete.*'),
    (2551, 'Can create own Role record',            66, 'role.own.create.*'),
    (2552, 'Can read own Role record',              66, 'role.own.read.*'),
    (2553, 'Can update own Role record',            66, 'role.own.update.*'),
    (2554, 'Can delete own Role record',            66, 'role.own.delete.*'),

    (2601, 'Can create any Source record',          67, 'source.any.create.*'),
    (2602, 'Can read any Source record',            67, 'source.any.read.*'),
    (2603, 'Can update any Source record',          67, 'source.any.update.*'),
    (2604, 'Can delete any Source record',          67, 'source.any.delete.*'),
    (2651, 'Can create own Source record',          67, 'source.own.create.*'),
    (2652, 'Can read own Source record',            67, 'source.own.read.*'),
    (2653, 'Can update own Source record',          67, 'source.own.update.*'),
    (2654, 'Can delete own Source record',          67, 'source.own.delete.*'),

    (2701, 'Can create any UserProfile record',     68, 'userprofile.any.create.*'),
    (2702, 'Can read any UserProfile record',       68, 'userprofile.any.read.*'),
    (2703, 'Can update any UserProfile record',     68, 'userprofile.any.update.*'),
    (2704, 'Can delete any UserProfile record',     68, 'userprofile.any.delete.*'),
    (2751, 'Can create own UserProfile record',     68, 'userprofile.own.create.*'),
    (2752, 'Can read own UserProfile record',       68, 'userprofile.own.read.*'),
    (2753, 'Can update own UserProfile record',     68, 'userprofile.own.update.*'),
    (2754, 'Can delete own UserProfile record',     68, 'userprofile.own.delete.*'),

    (2801, 'Can create any User record',            69, 'user.any.create.*'),
    (2802, 'Can read any User record',              69, 'user.any.read.*'),
    (2803, 'Can update any User record',            69, 'user.any.update.*'),
    (2804, 'Can delete any User record',            69, 'user.any.delete.*'),
    (2805, 'Can do any action on User',             69, 'user.any.action.*'),
    (2851, 'Can create own User record',            69, 'user.own.create.*'),
    (2852, 'Can read own User record',              69, 'user.own.read.*'),
    (2853, 'Can update own User record',            69, 'user.own.update.*'),
    (2854, 'Can delete own User record',            69, 'user.own.delete.*'),

    (2901, 'Can create any Zone record',            70, 'zone.any.create.*'),
    (2902, 'Can read any Zone record',              70, 'zone.any.read.*'),
    (2903, 'Can update any Zone record',            70, 'zone.any.update.*'),
    (2904, 'Can delete any Zone record',            70, 'zone.any.delete.*'),
    (2951, 'Can create own Zone record',            70, 'zone.own.create.*'),
    (2952, 'Can read own Zone record',              70, 'zone.own.read.*'),
    (2953, 'Can update own Zone record',            70, 'zone.own.update.*'),
    (2954, 'Can delete own Zone record',            70, 'zone.own.delete.*'),

    (3002, 'Can use any tool',                      50, 'tools.any.read.*'),
    (3012, 'Can use any tool',                      50, 'tools.any.read.*,!resubmission'),
    (3023, 'Can use show config tool',              50, 'tools.any.read.show_config'),
    (3052, 'Can use own tool',                      50, 'tools.own.read.*'),
    (3062, 'Can use own tool',                      50, 'tools.own.read.*,!resubmission,!advertiser_bidder_insight,!publisher_bidder_insight,!show_config');


INSERT INTO `auth_group` VALUES
    (21, 'Trading Desk Stakeholder'),
    (22, 'Trading Desk Campaign Supervisor'),
    (23, 'Trading Desk Campaign Manager'),
    (24, 'Trading Desk Account Manager'),
    (25, 'Manage Stakeholder'),
    (26, 'Manage Super User'),
    (27, 'Manage AdOps Head'),
    (28, 'Manage AdOps Supervisor'),
    (29, 'Manage AdOps CM'),
    (30, 'Manage Account Manager'),
    (31, 'Manage TD Account Manager'),
    (32, 'Manage Creative Approval'),
    (33, 'Advertiser'),
    (34, 'Publisher');

INSERT INTO `auth_group_permissions` (group_id, permission_id) VALUES
    -- Trading Desk ============================================================
    -- create any/own: 1001/1051
    -- read   any/own: 1002/1052    [*]
    -- read       own:      1062    [trading_desk_id,trading_desk]
    -- update any/own: 1003/1053    [*]
    -- update any    : 1013         [status]
    -- update any    : 1023         [*,!currency]
    -- action any/own: 1005/1055
                (21, 1052),                         -- 21: Trading Desk Stakeholder
                (22, 1062),                         -- 22: Trading Desk Campaign Supervisor
                (23, 1062),                         -- 23: Trading Desk Campaign Manager/Analysts
                (24, 1062),                         -- 24: Trading Desk Account Manager
                (25, 1002),                         -- 25: Manage Stakeholder
    (26, 1001), (26, 1002), (26, 1003),             -- 26: Manage Super User (Eng./Product)
                (27, 1002),                         -- 27: Manage AdOps Head
                (28, 1002),                         -- 28: Manage AdOps Supervisor
                (29, 1002),                         -- 29: Manage AdOps Analyst/CM
                (30, 1002),                         -- 30: Manage Account Manager
    (31, 1001), (31, 1002), (31, 1003),             -- 31: Manage TD Account Manager
    -- Agency ==================================================================
    -- create any/own: 1101/1151
    -- create     own: 1101/1161    [*,!trading_desk_id,!currency,!agency_key]
    -- read   any/own: 1102/1152    [*]
    -- read       own:      1162    [*,!currency,!agency_key]
    -- update any/own: 1103/1153    [*]
    -- update               1163    [*,!trading_desk_id,!currency,!agency_key]
    -- ipdate any    : 1113         [*,!currency,!agency_key]
    -- action any/own: 1105/1155
                (21, 1162),                         -- 21: Trading Desk Stakeholder
    (22, 1161), (22, 1162), (22, 1163),             -- 22: Trading Desk Campaign Supervisor
    (23, 1161), (23, 1162), (23, 1163),             -- 23: Trading Desk Campaign Manager/Analysts
    (24, 1161), (24, 1162), (24, 1163),             -- 24: Trading Desk Account Manager
                (25, 1102),             (25, 1115), -- 25: Manage Stakeholder
    (26, 1101), (26, 1102), (26, 1103), (26, 1115), -- 26: Manage Super User (Eng./Product)
    (27, 1101), (27, 1102), (27, 1103), (27, 1115), -- 27: Manage AdOps Head
    (28, 1101), (28, 1102), (28, 1103), (28, 1115), -- 28: Manage AdOps Supervisor
    (29, 1101), (29, 1102), (29, 1103), (29, 1115), -- 29: Manage AdOps Analyst/CM
    (30, 1101), (30, 1102), (30, 1103), (30, 1115), -- 30: Manage Account Manager
    (31, 1101), (31, 1102), (31, 1103), (31, 1115), -- 31: Manage TD Account Manager
    -- Advertiser ==============================================================
    -- create any/own: 1201/1251
    -- create     own:      1261    [*,!advertiser_key,!currency]
    -- read   any/own: 1202/1252    [*]
    -- read       own:      1262    [*,!advertiser_key,!currency]
    -- update any/own: 1203/1253    [*]
    -- update     own:      1263    [*,!advertiser_key,!currency,!agency_id]
    -- update any    : 1213         [*,!agency_id,!currency]
                (21, 1262),                         -- 21: Trading Desk Stakeholder
    (22, 1261), (22, 1262), (22, 1263),             -- 22: Trading Desk Campaign Supervisor
    (23, 1261), (23, 1262), (23, 1263),             -- 23: Trading Desk Campaign Manager/Analysts
    (24, 1261), (24, 1262), (24, 1263),             -- 24: Trading Desk Account Manager
                (25, 1202),             (25, 1205), -- 25: Manage Stakeholder
    (26, 1201), (26, 1202), (26, 1213), (26, 1205), -- 26: Manage Super User (Eng./Product)
    (27, 1201), (27, 1202), (27, 1213), (27, 1205), -- 27: Manage AdOps Head
    (28, 1201), (28, 1202), (28, 1213), (28, 1205), -- 28: Manage AdOps Supervisor
    (29, 1201), (29, 1202), (29, 1213), (29, 1205), -- 29: Manage AdOps Analyst/CM
                (30, 1202),             (30, 1205), -- 30: Manage Account Manager
                (31, 1202),             (31, 1205), -- 31: Manage TD Account Manager
    -- Campaign ==============================================================
    -- create any/own: 1301/1351
    -- read   any/own: 1302/1352    [*]
    -- update any/own: 1303/1353    [*]
    -- action any/own: 1305/1355    [*]
    -- update any/own: 1313         [*,!targeting]
    -- update any/own: 1323         [*,!priority]
    -- create     own       1361    [*,!targeting,!total_cost_cap,!daily_cost_cap,!total_loss_cap,!total_loss_cap,!priority'),
    -- read       own       1362    [*,!total_cost_cap,!daily_cost_cap,!total_loss_cap,!total_loss_cap,!priority,!targeting.min_slice,!targeting.max_slice'),
    -- update     own       1363    [*,!total_cost_cap,!daily_cost_cap,!total_loss_cap,!total_loss_cap,!priority,!targeting.min_slice,!targeting.max_slice'),
    -- action any/own: 1315         [*,!targeting_json_update]
                (21, 1362),                         -- 21: Trading Desk Stakeholder
    (22, 1361), (22, 1362), (22, 1363),             -- 22: Trading Desk Campaign Supervisor
    (23, 1361), (23, 1362), (23, 1363),             -- 23: Trading Desk Campaign Manager/Analysts
    (24, 1361), (24, 1362), (24, 1363),             -- 24: Trading Desk Account Manager
                (25, 1302),             (25, 1315), -- 25: Manage Stakeholder
    (26, 1301), (26, 1302), (26, 1303), (26, 1305), -- 26: Manage Super User (Eng./Product)
    (27, 1301), (27, 1302), (27, 1323), (27, 1315), -- 27: Manage AdOps Head
    (28, 1301), (28, 1302), (28, 1323), (28, 1315), -- 28: Manage AdOps Supervisor
    (29, 1301), (29, 1302), (29, 1323), (29, 1315), -- 29: Manage AdOps Analyst/CM
                (30, 1302),             (30, 1315), -- 30: Manage Account Manager
                (31, 1302),             (31, 1315), -- 31: Manage TD Account Manager
    -- AdGroup ==============================================================
    -- create any/own: 1401/1451
    -- create any      1411         [*,!priority]
    -- read   any/own: 1402/1452    [*]
    -- create     own       1461    [*,!targeting,!total_cost_cap,!daily_cost_cap,!daily_loss_cap,!total_loss_cap,!overridden,!priority]
    -- read       own       1462    [*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_rev_type,!revmap_rev_value,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice]
    -- read       own       1472    [*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice']
    -- update any      1413         [*,!priority]
    -- update     own       1463    [*,!total_cost_cap,!daily_cost_cap,!daily_loss_cap,!total_loss_cap,!overridden,!priority,!revmap_rev_type,!revmap_rev_value,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice]
    -- update     own       1473    [*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice'),


    -- update any/own: 1403/1453
    -- action any/own: 1405/1455    [*]
    -- action any      1415         [*,!bulk,!import,!targeting_json_update]
    -- action any      1425         [*,!targeting_json_update]
    -- action     own       1465    [*,!bulk,!import,!rates,!limits,!targeting_json_read,!targeting_json_update]
    -- action     own       1475    [*,!rates,!limits,!targeting_json_read,!targeting_json_update]
                (21, 1462),             (21, 1465), -- 21: Trading Desk Stakeholder
    (22, 1461), (22, 1472), (22, 1473), (22, 1475), -- 22: Trading Desk Campaign Supervisor
    (23, 1461), (23, 1472), (23, 1473), (23, 1475), -- 23: Trading Desk Campaign Manager/Analysts
    (24, 1461), (24, 1472), (24, 1473), (24, 1475), -- 24: Trading Desk Account Manager
                (25, 1402),             (25, 1415), -- 25: Manage Stakeholder
    (26, 1401), (26, 1402), (26, 1403), (26, 1405), -- 26: Manage Super User (Eng./Product)
    (27, 1411), (27, 1402), (27, 1413), (27, 1425), -- 27: Manage AdOps Head
    (28, 1411), (28, 1402), (28, 1413), (28, 1425), -- 28: Manage AdOps Supervisor
    (29, 1411), (29, 1402), (29, 1413), (29, 1425), -- 29: Manage AdOps Analyst/CM
                (30, 1402),             (30, 1415), -- 30: Manage Account Manager
                (31, 1402),             (31, 1415), -- 31: Manage TD Account Manager
    -- Ad      ==============================================================
    -- create any/own: 1501/1551
    -- read   any/own: 1502/1552    [*]
    -- create     own       1561    [*,!external_args'),
    -- read       own       1562    [*,!html,!external_args'),
    -- update     own       1563    [*,!external_args'),
    -- update any/own: 1503/1553
    -- action any/own  1571/1575    [*,!bulk_re_submit_to_adx,!bulk],
    -- action     own       1576    [*,!bulk_re_submit_to_adx']
                (21, 1562),             (21, 1575), -- 21: Trading Desk Stakeholder
    (22, 1551), (22, 1562), (22, 1553), (22, 1576), -- 22: Trading Desk Campaign Supervisor
    (23, 1551), (23, 1562), (23, 1553), (23, 1576), -- 23: Trading Desk Campaign Manager/Analysts
    (24, 1551), (24, 1562), (24, 1553), (24, 1576), -- 24: Trading Desk Account Manager
                (25, 1502),             (25, 1571), -- 25: Manage Stakeholder
    (26, 1501), (26, 1502), (26, 1503),             -- 26: Manage Super User (Eng./Product)
    (27, 1501), (27, 1502), (27, 1503),             -- 27: Manage AdOps Head
    (28, 1501), (28, 1502), (28, 1503),             -- 28: Manage AdOps Supervisor
    (29, 1501), (29, 1502), (29, 1503),             -- 29: Manage AdOps Analyst/CM
                (30, 1502),             (30, 1571), -- 30: Manage Account Manager
                (31, 1502),             (31, 1571), -- 31: Manage TD Account Manager
    -- User ==================================================================
    -- create any/own: 2801/2851
    -- read   any/own: 2802/2852    [*]
    -- update any/own: 2803/2853    [*]
    -- action any    : 2805
                (21, 2852),                         -- 21: Trading Desk Stakeholder
                (22, 2852),                         -- 22: Trading Desk Campaign Supervisor
                (23, 2852),                         -- 23: Trading Desk Campaign Manager/Analysts
    (24, 2851), (24, 2852), (24, 2853),             -- 24: Trading Desk Account Manager
                (25, 2802),             (25, 2805), -- 25: Manage Stakeholder
    (26, 2801), (26, 2802), (26, 2803), (26, 2805), -- 26: Manage Super User (Eng./Product)
                (27, 2802),             (27, 2805), -- 27: Manage AdOps Head
                (28, 2802),             (28, 2805), -- 28: Manage AdOps Supervisor
                (29, 2802),             (29, 2805), -- 29: Manage AdOps Analyst/CM
    (30, 2801), (30, 2802), (30, 2803), (30, 2805), -- 30: Manage Account Manager
    (31, 2801), (31, 2802), (31, 2803), (31, 2805), -- 31: Manage TD Account Manager

    -- Blacklist ==============================================================
    -- create any/own: 1801/1851
    -- read   any/own: 1802/1852    [*]
    -- read       own: 1852         [*]
    -- update any/own: 1803/1853    [*]
    -- delete any/own: 1804/1854
                                                    -- 21: Trading Desk Stakeholder
    (22, 1851), (22, 1852), (22, 1853), (22, 1854), -- 22: Trading Desk Campaign Supervisor
    (23, 1851), (23, 1852), (23, 1853), (23, 1854), -- 23: Trading Desk Campaign Manager/Analysts
    (24, 1851), (24, 1852), (24, 1853), (24, 1854), -- 24: Trading Desk Account Manager
                (25, 1802),                         -- 25: Manage Stakeholder
    (26, 1801), (26, 1802), (26, 1803), (26, 1804), -- 26: Manage Super User (Eng./Product)
    (27, 1801), (27, 1802), (27, 1803), (27, 1804), -- 27: Manage AdOps Head
    (28, 1801), (28, 1802), (28, 1803), (28, 1804), -- 28: Manage AdOps Supervisor
    (29, 1801), (29, 1802), (29, 1803), (29, 1804), -- 29: Manage AdOps Analyst/CM
                (30, 1802),                         -- 30: Manage Account Manager
                (31, 1802),                         -- 31: Manage TD Account Manager

    -- Whitelist ==============================================================
    -- create any/own: 1901/1951
    -- read   any/own: 1902/1952    [*]
    -- read       own: 1952         [*]
    -- update any/own: 1903/1953
    -- delete any/own: 1904/1954
                                                    -- 21: Trading Desk Stakeholder
    (22, 1951), (22, 1952), (22, 1953), (22, 1954), -- 22: Trading Desk Campaign Supervisor
    (23, 1951), (23, 1952), (23, 1953), (23, 1954), -- 23: Trading Desk Campaign Manager/Analysts
    (24, 1951), (24, 1952), (24, 1953), (24, 1954), -- 24: Trading Desk Account Manager
                (25, 1902),                         -- 25: Manage Stakeholder
    (26, 1901), (26, 1902), (26, 1903), (26, 1904), -- 26: Manage Super User (Eng./Product)
    (27, 1901), (27, 1902), (27, 1903), (27, 1904), -- 27: Manage AdOps Head
    (28, 1901), (28, 1902), (28, 1903), (28, 1904), -- 28: Manage AdOps Supervisor
    (29, 1901), (29, 1902), (29, 1903), (29, 1904), -- 29: Manage AdOps Analyst/CM
                (30, 1902),                         -- 30: Manage Account Manager
                (31, 1902),                         -- 31: Manage TD Account Manager

    -- CustomHints ==============================================================
    -- create any/own: 2001/2051
    -- read   any/own: 2002/2052    [*]
    -- read       own: 2052         [*]
    -- update any/own: 2003/2053
    -- delete any/own: 2004/2054
                                                    -- 21: Trading Desk Stakeholder
    (22, 2051), (22, 2052), (22, 2053), (22, 2054), -- 22: Trading Desk Campaign Supervisor
    (23, 2051), (23, 2052), (23, 2053), (23, 2054), -- 23: Trading Desk Campaign Manager/Analysts
    (24, 2051), (24, 2052), (24, 2053), (24, 2054), -- 24: Trading Desk Account Manager
                (25, 2002),                         -- 25: Manage Stakeholder
    (26, 2001), (26, 2002), (26, 2003), (26, 2004), -- 26: Manage Super User (Eng./Product)
    (27, 2001), (27, 2002), (27, 2003), (27, 2004), -- 27: Manage AdOps Head
    (28, 2001), (28, 2002), (28, 2003), (28, 2004), -- 28: Manage AdOps Supervisor
    (29, 2001), (29, 2002), (29, 2003), (29, 2004), -- 29: Manage AdOps Analyst/CM
                (30, 2002),                         -- 30: Manage Account Manager
                (31, 2002),                         -- 31: Manage TD Account Manager

    -- Events ===================================================================
    -- create any/own: 2101/2151
    -- read   any/own: 2102/2152
    -- update any/own: 2103/2153
                (21, 2152),                         -- 21: Trading Desk Stakeholder
    (22, 2151), (22, 2152), (22, 2153),             -- 22: Trading Desk Campaign Supervisor
    (23, 2151), (23, 2152), (23, 2153),             -- 23: Trading Desk Campaign Manager/Analysts
    (24, 2151), (24, 2152), (24, 2153),             -- 24: Trading Desk Account Manager
                (25, 2102),                         -- 25: Manage Stakeholder
    (26, 2101), (26, 2102), (26, 2103),             -- 26: Manage Super User (Eng./Product)
    (27, 2101), (27, 2102), (27, 2103),             -- 27: Manage AdOps Head
    (28, 2101), (28, 2102), (28, 2103),             -- 28: Manage AdOps Supervisor
    (29, 2101), (29, 2102), (29, 2103),             -- 29: Manage AdOps Analyst/CM
                (30, 2102),                         -- 30: Manage Account Manager
                (31, 2102),                         -- 31: Manage TD Account Manager

    -- AuditLogs ===============================================================
    -- read   any/own: 1702/1752    [*]
                (21, 1752),                         -- 21: Trading Desk Stakeholder
                (22, 1752),                         -- 22: Trading Desk Campaign Supervisor
                (23, 1752),                         -- 23: Trading Desk Campaign Manager/Analysts
                (24, 1752),                         -- 24: Trading Desk Account Manager
                (25, 1702),                         -- 25: Manage Stakeholder
                (26, 1702),                         -- 26: Manage Super User (Eng./Product)
                (27, 1702),                         -- 27: Manage AdOps Head
                (28, 1702),                         -- 28: Manage AdOps Supervisor
                (29, 1702),                         -- 29: Manage AdOps Analyst/CM
                (30, 1702),                         -- 30: Manage Account Manager
                (31, 1702),                         -- 31: Manage TD Account Manager

    -- Tools ===================================================================
    -- read   any/own: 3002/3052    [*]
    -- read       own:      3062    [*,!resubmission,!advertiser_bidder_insight,!publisher_bidder_insight]
    -- read       any:      3023    [show_config]
    -- read   any    : 3012         [*,!resubmission]
                                                    -- 21: Trading Desk Stakeholder
                (22, 3062),                         -- 22: Trading Desk Campaign Supervisor
                (23, 3062),                         -- 23: Trading Desk Campaign Manager/Analysts
                (24, 3062),                         -- 24: Trading Desk Account Manager
                (25, 3012), (25, 3023)              -- 25: Manage Stakeholder
                (26, 3002), (26, 3023)              -- 26: Manage Super User (Eng./Product)
                (27, 3002), (27, 3023)              -- 27: Manage AdOps Head
                (28, 3002), (28, 3023)              -- 28: Manage AdOps Supervisor
                (29, 3002), (29, 3023)              -- 29: Manage AdOps Analyst/CM
                (30, 3002), (30, 3023)              -- 30: Manage Account Manager
                (31, 3002); (31, 3023)              -- 31: Manage TD Account Manager


-- UPDATE User's ================================================================================================================
INSERT INTO `userprofile` (user_id)
    SELECT id FROM `auth_user` WHERE id NOT IN (SELECT user_id FROM `userprofile`);

INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id)
    SELECT id, 1 FROM `userprofile` WHERE id NOT IN (SELECT userprofile_id FROM `userprofile_trading_desks`);
