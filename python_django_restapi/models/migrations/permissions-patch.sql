UPDATE `auth_permission` SET `codename`='auditlog.any.create.*'        WHERE `id`=1701;
UPDATE `auth_permission` SET `codename`='auditlog.any.read.*'          WHERE `id`=1702;
UPDATE `auth_permission` SET `codename`='auditlog.any.update.*'        WHERE `id`=1703;
UPDATE `auth_permission` SET `codename`='auditlog.any.delete.*'        WHERE `id`=1704;
UPDATE `auth_permission` SET `codename`='auditlog.own.create.*'        WHERE `id`=1751;
UPDATE `auth_permission` SET `codename`='auditlog.own.read.*'          WHERE `id`=1752;
UPDATE `auth_permission` SET `codename`='auditlog.own.update.*'        WHERE `id`=1753;
UPDATE `auth_permission` SET `codename`='auditlog.own.delete.*'        WHERE `id`=1754;
UPDATE `auth_permission` SET `codename`='bidderblacklist.any.create.*' WHERE `id`=1801;
UPDATE `auth_permission` SET `codename`='bidderblacklist.any.read.*'   WHERE `id`=1802;
UPDATE `auth_permission` SET `codename`='bidderblacklist.any.update.*' WHERE `id`=1803;
UPDATE `auth_permission` SET `codename`='bidderblacklist.any.delete.*' WHERE `id`=1804;
UPDATE `auth_permission` SET `codename`='bidderblacklist.own.create.*' WHERE `id`=1851;
UPDATE `auth_permission` SET `codename`='bidderblacklist.own.read.*'   WHERE `id`=1852;
UPDATE `auth_permission` SET `codename`='bidderblacklist.own.update.*' WHERE `id`=1853;
UPDATE `auth_permission` SET `codename`='bidderblacklist.own.delete.*' WHERE `id`=1854;
UPDATE `auth_permission` SET `codename`='bidderwhitelist.any.create.*' WHERE `id`=1901;
UPDATE `auth_permission` SET `codename`='bidderwhitelist.any.read.*'   WHERE `id`=1902;
UPDATE `auth_permission` SET `codename`='bidderwhitelist.any.update.*' WHERE `id`=1903;
UPDATE `auth_permission` SET `codename`='bidderwhitelist.any.delete.*' WHERE `id`=1904;
UPDATE `auth_permission` SET `codename`='bidderwhitelist.own.create.*' WHERE `id`=1951;
UPDATE `auth_permission` SET `codename`='bidderwhitelist.own.read.*'   WHERE `id`=1952;
UPDATE `auth_permission` SET `codename`='bidderwhitelist.own.update.*' WHERE `id`=1953;
UPDATE `auth_permission` SET `codename`='bidderwhitelist.own.delete.*' WHERE `id`=1954;
UPDATE `auth_permission` SET `codename`='customhint.any.create.*'      WHERE `id`=2001;
UPDATE `auth_permission` SET `codename`='customhint.any.read.*'        WHERE `id`=2002;
UPDATE `auth_permission` SET `codename`='customhint.any.update.*'      WHERE `id`=2003;
UPDATE `auth_permission` SET `codename`='customhint.any.delete.*'      WHERE `id`=2004;
UPDATE `auth_permission` SET `codename`='customhint.own.create.*'      WHERE `id`=2051;
UPDATE `auth_permission` SET `codename`='customhint.own.read.*'        WHERE `id`=2052;
UPDATE `auth_permission` SET `codename`='customhint.own.update.*'      WHERE `id`=2053;
UPDATE `auth_permission` SET `codename`='customhint.own.delete.*'      WHERE `id`=2054;

-- bidder_black_list
INSERT INTO `auth_group_permissions` (`group_id`,`permission_id`) VALUES
    (22,1851),(22,1852),(22,1853),(23,1851),(23,1852),(23,1853),(24,1851),(24,1852),
    (24,1853),(25,1802),(26,1801),(26,1802),(26,1803),(27,1801),(27,1802),(27,1803),
    (28,1801),(28,1802),(28,1803),(29,1801),(29,1802),(29,1803),(30,1802),(31,1802);

-- bidder_black_list
INSERT INTO `auth_group_permissions` (`group_id`,`permission_id`) VALUES
    (22,1951),(22,1952),(22,1953),(23,1951),(23,1952),(23,1953),(24,1951),(24,1952),
    (24,1953),(25,1902),(26,1901),(26,1902),(26,1903),(27,1901),(27,1902),(27,1903),
    (28,1901),(28,1902),(28,1903),(29,1901),(29,1902),(29,1903),(30,1902),(31,1902);

-- custom_hint
INSERT INTO `auth_group_permissions` (`group_id`,`permission_id`) VALUES
    (22,2051),(22,2052),(22,2053),(23,2051),(23,2052),(23,2053),(24,2051),(24,2052),
    (24,2053),(25,2002),(26,2001),(26,2002),(26,2003),(27,2001),(27,2002),(27,2003),
    (28,2001),(28,2002),(28,2003),(29,2001),(29,2002),(29,2003),(30,2002),(31,2002);
