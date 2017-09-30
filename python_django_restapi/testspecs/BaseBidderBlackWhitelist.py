from restapi.models.Campaign import Campaign
from restapi.models.AdGroup import AdGroup
from restapi.models.Source import Source
from restapi.models.BidderBlacklist import BidderBlacklistIds
from restapi.models.BidderWhitelist import BidderWhitelistIds
from restapi.testspecs.CreateTestData import CreateTestData


class BaseBidderBlackWhitelist(CreateTestData):
    advertiser = None
    campaign = None
    ad_group = None
    source = None

    def _create_dependency_objects(self):
        self.advertiser = self.create_advertiser()

        self.campaign = Campaign(advertiser_id=self.advertiser, campaign='campaign 1', genre=1)
        self.campaign.save()

        self.ad_group = AdGroup(campaign_id=self.campaign, ad_group='ad group 1')
        self.ad_group.save()

        self.source = Source(source='Facebook', class_value='mobile')
        self.source.save()

        self.source1 = Source(source='Twitter', class_value='mobile')
        self.source1.save()

        self.source2 = Source(source='Vk', class_value='mobile')
        self.source2.save()

    # pylint: disable=no-self-use
    def _create_black_list_entry(self, campaign_id, ad_group_id, source_id):
        bidder = BidderBlacklistIds(campaign_id=campaign_id,
                                    ad_group_id=ad_group_id,
                                    source_id=source_id,
                                    placement_type='app',
                                    size='0x0',
                                    placement_id='-1.00071E+18',
                                    tag='LowCTR-20150513')
        bidder.save()
        return bidder

    # pylint: disable=no-self-use
    def _create_white_list_entry(self, campaign_id, ad_group_id, source_id):
        bidder = BidderWhitelistIds(campaign_id=campaign_id,
                                    ad_group_id=ad_group_id,
                                    source_id=source_id,
                                    placement_type='app',
                                    size='0x0',
                                    placement_id='-1.00071E+18',
                                    tag='LowCTR-20150513')
        bidder.save()
        return bidder

    # pylint: disable=no-self-use
    def _build_request_1(self, bidder_list1, bidder_list2, bidder_list3):
        return {'delete': [],
                'save': [
                    {
                        'campaign_id': 0,
                        'ad_group_id': 0,
                        'source_id': bidder_list1.source_id,
                        'placement_type': u'site',
                        'placement_id': u'test_update_placement_id',
                        'tag': u'test_update_tag'
                    }],
                'patch': [
                    {
                        'id': bidder_list1.pk,
                        'campaign_id': bidder_list1.campaign_id,
                        'ad_group_id': bidder_list1.ad_group_id,
                        'source_id': bidder_list1.source_id,
                        'placement_type': u'site',
                        'placement_id': u'test_update_placement_id',
                        'tag': u'test_update_tag'
                    },
                    {
                        'id': bidder_list2.pk,
                        'campaign_id': bidder_list2.campaign_id,
                        'ad_group_id': bidder_list2.ad_group_id,
                        'source_id': bidder_list2.source_id,
                        'placement_type': u'site',
                        'placement_id': u'test_update_placement_id',
                        'tag': u'test_update_tag'
                    },
                    {
                        'id': bidder_list3.pk,
                        'campaign_id': bidder_list3.campaign_id,
                        'ad_group_id': bidder_list3.ad_group_id,
                        'source_id': bidder_list3.source_id,
                        'placement_type': u'site',
                        'placement_id': u'test_update_placement_id',
                        'tag': u'test_update_tag'
                    }
                ]}

    # pylint: disable=no-self-use
    def _build_request_2(self, bidder_list1, bidder_list2):
        return {'delete': [],
                'save': [
                    {   # NORMAL
                        'campaign_id': bidder_list1.campaign_id,
                        'ad_group_id': bidder_list1.ad_group_id,
                        'source_id': bidder_list1.source_id,
                        'placement_type': u'site',
                        'placement_id': u'test_update_placement_id',
                        'tag': u'test_tag'
                    },
                    {   # NORMAL
                        'id': bidder_list1.pk,
                        'campaign_id': bidder_list1.campaign_id,
                        'ad_group_id': bidder_list1.ad_group_id,
                        'source_id': bidder_list1.source_id,
                        'placement_type': u'site',
                        'placement_id': u'test_update_placement_id',
                        'tag': u'test_tag'
                    },
                    {   #BAD
                        'campaign_id': bidder_list2.campaign_id,
                        'ad_group_id': bidder_list2.ad_group_id,
                        'source_id': bidder_list2.source_id,
                        'placement_type': u'',
                        'placement_id': u'test_update_placement_id',
                        'tag': u'test_tag'
                    }]}
