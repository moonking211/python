CREATE TABLE `io` (
  `io_id` int(10) UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
  `start_date` datetime NOT NULL,
  `end_date` datetime NOT NULL,
  `io_budget` double precision NOT NULL,
  `io_document_link` varchar(1024) NOT NULL,
  `notes` longtext NOT NULL,
  `advertiser_id` int(10) UNSIGNED NOT NULL)
ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `restapi_io_campaign` (
  `id` int(10) UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
  `join_date` datetime NOT NULL,
  `campaign_id` int(10) UNSIGNED NOT NULL,
  `io_id` int(10) UNSIGNED NOT NULL)
ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE INDEX io_3cc7577e ON `io` (`advertiser_id`);

ALTER TABLE `io`
ADD CONSTRAINT io_advertiser_id_13d50063057d5ed_fk_advertiser_advertiser_id
FOREIGN KEY (`advertiser_id`)
REFERENCES `advertiser` (`advertiser_id`);


CREATE INDEX restapi_io_campaign_f14acec3 ON `restapi_io_campaign` (`campaign_id`);

ALTER TABLE `restapi_io_campaign`
ADD CONSTRAINT restapi_io__campaign_id_4d88a25e0d8e3f2d_fk_campaign_campaign_id
FOREIGN KEY (`campaign_id`)
REFERENCES `campaign` (`campaign_id`);


CREATE INDEX restapi_io_campaign_63a059b0 ON `restapi_io_campaign` (`io_id`);

ALTER TABLE `restapi_io_campaign`
ADD CONSTRAINT restapi_io_campaign_io_id_49611a27015b4267_fk_io_io_id
FOREIGN KEY (`io_id`)
REFERENCES `io` (`io_id`);

