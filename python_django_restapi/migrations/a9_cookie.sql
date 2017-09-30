CREATE TABLE `a9_cookie` (
  `cookie_id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `authenticity_token` varchar(255) NOT NULL DEFAULT '',
  `cookie_text` text NOT NULL,
  PRIMARY KEY (`cookie_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;