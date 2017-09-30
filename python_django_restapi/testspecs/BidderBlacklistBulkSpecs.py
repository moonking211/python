from rest_framework.exceptions import ValidationError

from restapi.views.bidder_black_list.BidderBlacklistBulk import BidderBlacklistBulk
from restapi.testspecs.BaseBidderBlackWhitelist import BaseBidderBlackWhitelist
from restapi.models.BidderBlacklist import BidderBlacklistIds
from restapi.models.BidderBlacklist import AUDIT_TYPE_BIDDER_BLACK_LIST
from restapi.models.AuditLog import AUDIT_ACTION_ADD, AUDIT_ACTION_UPDATE, AUDIT_ACTION_DELETE
from restapi.models.AuditLog import AuditLog

from mng.test import spec
from mock import Mock


class BidderBlacklistBulkSpecs(spec(BidderBlacklistBulk), BaseBidderBlackWhitelist):
    bidder_black_list_service = None
    bidder_blacklist1 = None
    bidder_blacklist2 = None
    bidder_blacklist3 = None

    source = None
    request = None
    subject = None

    def before_each(self):
        self._create_client()
        self._create_dependency_objects()

        self.bidder_blacklist1 = self._create_black_list_entry(self.campaign.pk, self.ad_group.pk, self.source.pk)
        self.bidder_blacklist2 = self._create_black_list_entry(self.campaign.pk, self.ad_group.pk, self.source1.pk)
        self.bidder_blacklist3 = self._create_black_list_entry(self.campaign.pk, self.ad_group.pk, self.source2.pk)

        bidder_service = Mock()
        request = Mock()
        request.QUERY_PARAMS = {}

        self.request = request
        self.bidder_black_list_service = bidder_service
        self.subject = BidderBlacklistBulk(bidder_service=lambda: bidder_service)

    def test__post__bidder_black_list_bulk_edit(self):
        # pylint: disable=no-member
        self.assertEqual(3, BidderBlacklistIds.objects.count())

        self.request.DATA = self._build_request_1(self.bidder_blacklist1,
                                                  self.bidder_blacklist2,
                                                  self.bidder_blacklist3)
        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, 200)
        # pylint: disable=no-member
        self.assertEqual(4, BidderBlacklistIds.objects.count())

        for entry in list(BidderBlacklistIds.objects.all()):
            self.assertEqual(entry.placement_type, 'site')
            self.assertEqual(entry.placement_id, 'test_update_placement_id')
            self.assertEqual(entry.tag, 'test_update_tag')

        audit_qs = AuditLog.objects.filter(audit_type=AUDIT_TYPE_BIDDER_BLACK_LIST)
        self.assertTrue(len(audit_qs) > 0)

        self.bidder_blacklist3.delete()
        for audit in audit_qs:
            self.assertTrue(audit.audit_type, AUDIT_TYPE_BIDDER_BLACK_LIST)
            self.assertTrue(audit.audit_action == AUDIT_ACTION_ADD or
                            audit.audit_action == AUDIT_ACTION_UPDATE or
                            audit.audit_action == AUDIT_ACTION_DELETE)

    def test__post__bidder_black_list_bulck_edit_validation_error(self):
        # pylint: disable=no-member
        self.assertEqual(3, BidderBlacklistIds.objects.count())

        self.request.DATA = self._build_request_2(self.bidder_blacklist1, self.bidder_blacklist2)
        self.assertRaises(ValidationError, self.subject.post, self.request)

        # Without transaction should be 5 rows but after roll back stay 3 as into begining
        # pylint: disable=no-member
        self.assertEqual(3, BidderBlacklistIds.objects.count())
