DROP VIEW IF EXISTS discrete_pricing_view;
CREATE VIEW discrete_pricing_view AS
    SELECT ch.*,
        IFNULL(ag.ad_group, "") ad_group,
        IFNULL(c.campaign, "") campaign,
        IFNULL(s.source, "") source,
        IFNULL(c.advertiser_id, 0) advertiser_id
    FROM discrete_pricing ch
    LEFT JOIN campaign c on c.campaign_id=ch.campaign_id
    LEFT JOIN ad_group ag on ag.ad_group_id=ch.ad_group_id
    LEFT JOIN source s on s.source_id=ch.source_id;
