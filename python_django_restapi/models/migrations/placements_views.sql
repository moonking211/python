DROP VIEW IF EXISTS bidder_blacklist_view;
CREATE VIEW bidder_blacklist_view AS
    SELECT bb.*,
        IFNULL(ag.ad_group, "") ad_group,
        IFNULL(c.campaign, "") campaign,
        IFNULL(s.source, "") source,
        IFNULL(c.advertiser_id, 0) advertiser_id
    FROM bidder_blacklist bb
    LEFT JOIN campaign c on c.campaign_id=bb.campaign_id
    LEFT JOIN ad_group ag on ag.ad_group_id=bb.ad_group_id
    LEFT JOIN source s on s.source_id=bb.source_id;

DROP VIEW IF EXISTS bidder_whitelist_view;
CREATE VIEW bidder_whitelist_view AS
    SELECT bw.*,
        IFNULL(ag.ad_group, "") ad_group,
        IFNULL(c.campaign, "") campaign,
        IFNULL(s.source, "") source,
        IFNULL(c.advertiser_id, 0) advertiser_id
    FROM bidder_whitelist bw
    LEFT JOIN campaign c on c.campaign_id=bw.campaign_id
    LEFT JOIN ad_group ag on ag.ad_group_id=bw.ad_group_id
    LEFT JOIN source s on s.source_id=bw.source_id;

DROP VIEW IF EXISTS custom_hint_view;
CREATE VIEW custom_hint_view AS
    SELECT ch.*,
        IFNULL(ag.ad_group, "") ad_group,
        IFNULL(c.campaign, "") campaign,
        IFNULL(s.source, "") source,
        IFNULL(c.advertiser_id, 0) advertiser_id,
        IFNULL(a.ad, "") ad
    FROM custom_hint ch
    LEFT JOIN campaign c on c.campaign_id=ch.campaign_id
    LEFT JOIN ad_group ag on ag.ad_group_id=ch.ad_group_id
    LEFT JOIN source s on s.source_id=ch.source_id
    LEFT JOIN ad a on a.ad_id=ch.ad_id;
