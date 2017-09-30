CREATE TABLE `tw_tv_market` (
  `tw_tv_market_id` int(10) NOT NULL,
  `country_code` varchar(2) NOT NULL DEFAULT '',
  `name` varchar(30) NOT NULL DEFAULT '',
  `locale` varchar(7) NOT NULL DEFAULT '',
  PRIMARY KEY (`tw_tv_market_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `tw_tv_genre` (
  `tw_tv_genre_id` int(10) NOT NULL,
  `name` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`tw_tv_genre_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `tw_tv_channel` (
  `tw_tv_channel_id` int(10) NOT NULL,
  `name` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`tw_tv_channel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `tw_tv_channel_market` (
  `tw_tv_channel_id` int(10) NOT NULL,
  `tw_tv_market_id` int(10) NOT NULL,
  INDEX tw_tv_channel_index (tw_tv_channel_id),
  FOREIGN KEY (tw_tv_channel_id) REFERENCES tw_tv_channel(tw_tv_channel_id),
  INDEX tw_tv_market_index(tw_tv_market_id),
  FOREIGN KEY (tw_tv_market_id) REFERENCES tw_tv_market(tw_tv_market_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


