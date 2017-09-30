ALTER TABLE `advertiser`
    ADD `currency` CHAR(3) NOT NULL,
    ADD `discount` DECIMAL(9,2) NOT NULL DEFAULT 0;

-- Display and Richmedia
SET @ad_group_type = 1;
UPDATE ad_group ag SET ag.ad_group_type = ad_group_type
WHERE ag.ad_group_type = @ad_group_type AND @ad_group_type = ALL(
    SELECT IF(a2.ad_type=6, @ad_group_type, a2.ad_type) from ad a2 WHERE a2.ad_group_id=ag.ad_group_id
);

-- Video
SET @ad_group_type = 2;
UPDATE ad_group ag SET ag.ad_group_type = ad_group_type
WHERE ag.ad_group_type = @ad_group_type AND @ad_group_type = ALL(SELECT a2.ad_type from ad a2 WHERE a2.ad_group_id=ag.ad_group_id);

-- Experience
SET @ad_group_type = 3;
UPDATE ad_group ag SET ag.ad_group_type = ad_group_type
WHERE ag.ad_group_type = @ad_group_type AND @ad_group_type = ALL(SELECT a2.ad_type from ad a2 WHERE a2.ad_group_id=ag.ad_group_id);

-- MRAID
SET @ad_group_type = 4;
UPDATE ad_group ag SET ag.ad_group_type = ad_group_type
WHERE ag.ad_group_type = @ad_group_type AND @ad_group_type = ALL(SELECT a2.ad_type from ad a2 WHERE a2.ad_group_id=ag.ad_group_id);

-- Native
SET @ad_group_type = 5;
UPDATE ad_group ag SET ag.ad_group_type = ad_group_type
WHERE ag.ad_group_type = @ad_group_type AND @ad_group_type = ALL(SELECT a2.ad_type from ad a2 WHERE a2.ad_group_id=ag.ad_group_id);
