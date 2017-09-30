# coding=utf8
# pylint: disable=unused-import
# noinspection PyUnresolvedReferences
import os

mm_test = os.environ.get('MM_TEST') or 'all'

try:
    # REMARK: Order imports in alphanum

    if mm_test in ['all', 'integration']:
        from restapi.testspecs.AdBulkSpec import AdBulkSpec
        from restapi.testspecs.AdGroupBulkSpec import AdGroupBulkSpec
        from restapi.testspecs.AdGroupSpecs import AdGroupTest
        from restapi.testspecs.AdSpecs import AdTest
        from restapi.testspecs.AdsResubmitSpec import AdsResubmitSpec
        from restapi.testspecs.AdGroupServiceSpecs import AdGroupsReplicateSpec
        from restapi.testspecs.AdvertiserSpecs import AdvertiserTest
        from restapi.testspecs.AgencySpecs import AgencySpecs
        from restapi.testspecs.BidderBlacklistBulkSpecs import BidderBlacklistBulkSpecs
        from restapi.testspecs.BidderWhitelistBulkSpecs import BidderWhitelistBulkSpecs
        from restapi.testspecs.BaseModelSerializerSpecs import BaseModelSerializerSpecs
        from restapi.testspecs.CampaignSpecs import CampaignTest
        from restapi.testspecs.CustomHintBulkSpec import CustomHintBulkSpec
        from restapi.testspecs.DateTimeSpecs import DateTimeTest
        from restapi.testspecs.EventSpecs import EventTest
        from restapi.testspecs.FilterByListMixinSpecs import FilterByListMixinSpecs
        from restapi.testspecs.ListPaginationSpecs import ListPaginationSpecs
        from restapi.testspecs.TradingDeskSpecs import TradingDeskSpecs
        from restapi.testspecs.resources.AdGroupsChangeStatusSpecs import AdGroupsChangeStatusSpecs
        from restapi.testspecs.resources.AdsChangeStatusSpecs import AdsChangeStatusSpecs
        from restapi.testspecs.resources.AdsReplicateSpecs import AdsReplicateSpecs
        # temporary disabled
        # from restapi.testspecs.resources.BlobsSpecs import BlobsSpecs

    if mm_test in ['all', 'unit']:
        from restapi.testspecs.unittest.middleware_specs import Middleware
        from restapi.testspecs.unittest.time_shifting_specs import TimeShiftingTestCase
        from restapi.testspecs.unittest.serializers.AdGroupSerializer_specs import AdGroupSerializerSpecs
        from restapi.testspecs.unittest.views.account_manager.AccountManagerList_specs import AccountManagerListSpecs
        from restapi.testspecs.unittest.views.account_manager.AccountManagerDetail_specs import \
            AccountManagerDetailSpecs
        from restapi.testspecs.unittest.views.advertiser.AdvertiserList_specs import AdvertiserListSpecs
        from restapi.testspecs.unittest.views.advertiser.AdvertiserDetail_specs import AdvertiserDetailSpecs
        from restapi.testspecs.unittest.views.agency.AgencyList_specs import AgencyListSpecs
        from restapi.testspecs.unittest.views.agency.AgencyDetail_specs import AgencyDetailSpecs
        from restapi.testspecs.unittest.views.audit_log.AuditLogList_specs import AuditLogListSpecs
        from restapi.testspecs.unittest.views.audit_log.AuditLogDetail_specs import AuditLogDetailSpecs
        from restapi.testspecs.unittest.views.campaign.CampaignList_specs import CampaignListSpecs
        from restapi.testspecs.unittest.views.campaign.CampaignDetail_specs import CampaignDetailSpecs
        from restapi.testspecs.unittest.serializers.CampaignSerializer_specs import CampaignSerializerSpecs
        from restapi.testspecs.unittest.views.trading_desk.TradingDeskList_specs import TradingDeskListSpecs
        from restapi.testspecs.unittest.views.trading_desk.TradingDeskDetail_specs import TradingDeskDetailSpecs
        from restapi.testspecs.unittest.views.user.UserList_specs import UserListViewsSpecs
        from restapi.testspecs.unittest.views.user.UserDetail_specs import UserDetailViewsSpecs
        from restapi.testspecs.unittest.views.user.UserSave_specs import UserSaveSpecs
        from restapi.testspecs.unittest.views.user.UserSetPassword_specs import UserSetPasswordSpecs

    if mm_test in ['all', 'integration']:
        from restapi.testspecs.resources.TranscodingSpecs import TranscodingSpecs
        from restapi.testspecs.transcoding.TranscodingFactorySpecs import TranscodingFactorySpecs
        from restapi.testspecs.RevmapsSpec import RevmapsSpec

        # todo auto-discovery
except Exception:
    import sys
    import traceback

    sys.stdout.write('restapi.tests: failed to import modules\n')
    traceback.print_exc()
    raise Exception('restapi.tests: failed to import modules')
