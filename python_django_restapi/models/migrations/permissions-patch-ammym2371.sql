INSERT INTO `auth_permission` VALUES
    (1472, 'Can read own AdGroup record*',          55, 'adgroup.own.read.*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice'),
    (1473, 'Can update own AdGroup record*',        55, 'adgroup.own.update.*,!total_cost_cap,!daily_loss_cap,!daily_cost_cap,!total_loss_cap,!overridden,!priority,!revmap_opt_type,!revmap_opt_value,!targeting.min_slice,!targeting.max_slice');

UPDATE `auth_group_permissions` SET permission_id=1472 WHERE permission_id=1462 AND group_id in (22,23,24);
UPDATE `auth_group_permissions` SET permission_id=1473 WHERE permission_id=1463 AND group_id in (22,23,24);
