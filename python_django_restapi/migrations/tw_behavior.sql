CREATE TABLE `tw_behavior_taxonomy` (
  `tw_behavior_taxonomy_id` int(20) NOT NULL,
  `name` varchar(255) NOT NULL,
  `US` tinyint(1) DEFAULT '0',
  `GB` tinyint(1) DEFAULT '0',
  `parent_taxonomy_id` int(20) DEFAULT NULL,
  PRIMARY KEY (`tw_behavior_taxonomy_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `tw_behavior` (
  `tw_behavior_id` int(20) NOT NULL,
  `tw_behavior_taxonomy_id` int(20) NOT NULL,
  `country_code` varchar(2) NOT NULL,
  `name` varchar(255) NOT NULL DEFAULT '',
  `audience_size` int(20) DEFAULT '0',
  `partner_source` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`tw_behavior_id`),
  KEY `tw_behavior_taxonomy_index` (`tw_behavior_taxonomy_id`),
  CONSTRAINT `tw_behavior_ibfk_1` FOREIGN KEY (`tw_behavior_taxonomy_id`) REFERENCES `tw_behavior_taxonomy` (`tw_behavior_taxonomy_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;