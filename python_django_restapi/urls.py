from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns

from restapi.views.BidderInsight import BidderInsight
from restapi.views.ConfigView import ConfigView
from restapi.views.account_manager.AccountManagerList import AccountManagerList
from restapi.views.account_manager.AccountManagerDetail import AccountManagerDetail
from restapi.views.ad.AdDetail import AdDetail
from restapi.views.ad.AdList import AdList
from restapi.views.ad.AdBulk import AdBulk
from restapi.views.ad.AdsChangeStatus import AdsChangeStatus
from restapi.views.ad.AdsReplicate import AdsReplicate
from restapi.views.ad.AdsResubmit import AdsResubmit
from restapi.views.ad.AdDisapproved import AdDisapproved
from restapi.views.ad.mraid_ad.MraidAdTemplateDetail import MraidAdTemplateDetail
from restapi.views.ad.mraid_ad.MraidAdTemplateList import MraidAdTemplateList
from restapi.views.ad import AdPruningRecommendation
from restapi.views.ad_group.AdGroupDetail import AdGroupDetail
from restapi.views.ad_group.AdGroupList import AdGroupList
from restapi.views.ad_group.AdGroupsChangeStatus import AdGroupsChangeStatus
from restapi.views.ad_group.AdGroupsReplicate import AdGroupsReplicate
from restapi.views.ad_group.AdGroupsImport import AdGroupsImport
from restapi.views.advertiser.AdvertiserDetail import AdvertiserDetail
from restapi.views.advertiser.AdvertiserList import AdvertiserList
from restapi.views.advertiser.AdvertiserList import RawAdvertiserList
from restapi.views.advertiser.AdvertiserBulk import AdvertiserBulk
from restapi.views.agency.AgencyDetail import AgencyDetail
from restapi.views.agency.AgencyList import AgencyList
from restapi.views.audit_log.AuditLogDetail import AuditLogDetail
from restapi.views.audit_log.AuditLogList import AuditLogList
from restapi.views.bidder_black_list.BidderBlacklistDelete import BidderBlacklistDelete
from restapi.views.bidder_white_list.BidderWhitelistDelete import BidderWhitelistDelete
from restapi.views.campaign.CampaignDetail import CampaignDetail, TWCampaignDetail
from restapi.views.campaign.CampaignList import CampaignList, TWCampaignList
from restapi.views.currency.CurrencyDetail import CurrencyDetail
from restapi.views.currency.CurrencyList import CurrencyList
from restapi.views.campaign.CampaignBulk import CampaignBulk
from restapi.views.custom_hint.CustomHintDelete import CustomHintDelete
from restapi.views.discrete_pricing.DiscretePricingDelete import DiscretePricingDelete
from restapi.views.io.IoDetail import IoDetail
from restapi.views.io.IoList import IoList
from restapi.views.trading_desk.TradingDeskDetail import TradingDeskDetail
from restapi.views.trading_desk.TradingDeskList import TradingDeskList
from restapi.views.event.EventDetail import EventDetail
from restapi.views.event.EventList import EventList
from restapi.views.Blobs import Blobs
from restapi.views.InitList import InitList
from restapi.views.Search import Search, SearchLive
from restapi.views.Transcoding import Transcoding
# from restapi.views.revmap.RevmapList import RevmapList
# from restapi.views.revmap.RevmapDetail import RevmapDetail
from restapi.views.revmap.RevmapsUpdateAll import RevmapsUpdateAll
# from restapi.views.manage_user.ManageUserList import ManageUserList
# from restapi.views.manage_user.ManageUserDetail import ManageUserDetail
from restapi.views.user.UserList import UserList
from restapi.views.user.UserDetail import UserDetail
from restapi.views.user.UserSetPassword import UserSetPassword
from restapi.views.ad_group.AdGroupBulk import AdGroupBulk
from restapi.views.bidder_black_list.BidderBlacklistDetail import BidderBlacklistDetail
from restapi.views.bidder_black_list.BidderBlacklistList import BidderBlacklistList
from restapi.views.bidder_white_list.BidderWhitelistDetail import BidderWhitelistDetail
from restapi.views.bidder_white_list.BidderWhitelistList import BidderWhitelistList
from restapi.views.bidder_black_list.BidderBlacklistBulk import BidderBlacklistBulk
from restapi.views.bidder_white_list.BidderWhitelistBulk import BidderWhitelistBulk
from restapi.views.custom_hint.CustomHintDetail import CustomHintDetail
from restapi.views.custom_hint.CustomHintList import CustomHintList
from restapi.views.custom_hint.CustomHintBulk import CustomHintBulk
from restapi.views.discrete_pricing.DiscretePricingDetail import DiscretePricingDetail
from restapi.views.discrete_pricing.DiscretePricingList import DiscretePricingList
from restapi.views.discrete_pricing.DiscretePricingBulk import DiscretePricingBulk

from restapi.views.twitter.TwitterUserList import TwitterUserList
from restapi.views.twitter.TwitterUserDetail import TwitterUserDetail
from restapi.views.twitter.TwitterCampaignValidateApi import TwitterCampaignValidateApi
from restapi.views.twitter.TwitterAccountList import TwitterAccountList, RawTwitterAccountList
from restapi.views.twitter.TwitterAccountDelete import TwitterAccountDelete
from restapi.views.twitter.TwitterAccountDetail import TwitterAccountDetail
from restapi.views.twitter.TwitterAccountApi import TwitterAddAccountApi, TwitterSyncApi, TwitterAccessTokenApi, \
    TWitterCallbackApi, TwitterLiveAccountsApi
from restapi.views.twitter.TwitterCampaignList import TwitterCampaignList
from restapi.views.twitter.TwitterCampaignDetailApi import TwitterCampaignDetail
from restapi.views.twitter.TwitterLineItemList import TwitterLineItemList
from restapi.views.twitter.TwitterLineItemBulk import TwitterLineItemBulk
from restapi.views.twitter.TwitterLineItemDetail import TwitterLineItemDetail
from restapi.views.twitter.TwitterLineItemApi import TwitterLineItemApi
from restapi.views.twitter.TwitterFundingInstrumentApi import TwitterFundingInstrumentApi, TwitterFundingInstrumentListView
from restapi.views.twitter.TwitterAccountAppList import TwitterAccountAppList
from restapi.views.twitter.TwitterTargetingViewSet import *
from restapi.views.twitter.TwitterPromotedTweetList import TwitterPromotedTweetList
from restapi.views.twitter.TwitterPromotedTweetDetail import TwitterPromotedTweetDetail
from restapi.views.twitter.TwitterPromotedTweetApi import TwitterPromotedTweetApi, TwitterPromotableUserApi
from restapi.views.twitter.TwitterAppCardList import TwitterAppCardList
from restapi.views.twitter.TwitterAppCardDetail import TwitterAppCardDetail
from restapi.views.twitter.TwitterTweetList import TwitterTweetList
from restapi.views.twitter.TwitterTweetDetail import TwitterTweetDetail
from restapi.views.twitter.TwitterCampaignGenerateApi import TwitterCampaignGenerateApi
from restapi.views.twitter.TwitterRevmapList import TwitterRevmapList
from restapi.views.twitter.TwitterRevmapDetail import TwitterRevmapDetail
from restapi.views.twitter.TwitterTailoredAudienceList import TwitterTailoredAudienceList
from restapi.views.twitter.TwitterTailoredAudienceDetail import TwitterTailoredAudienceDetail
from restapi.views.twitter.TwitterFileDownloadApi import TwitterFileDownloadApi
from restapi.views.twitter.TwitterKeywordRecommendationApi import TwitterKeywordRecommendationApi
from restapi.views.twitter.TwitterHandleRecommendationApi import TwitterHandleRecommendationApi
from restapi.views.twitter.TwitterReachEstimateApi import TwitterReachEstimateApi
from restapi.views.twitter.TwitterTVShowApi import TwitterTVShowApi
from restapi.views.twitter.TwitterUserApi import TwitterUserSearchApi, TwitterUsersVerifyApi
from restapi.views.twitter.TwitterWebEventTagApi import TwitterWebEventTagApi
from restapi.views.twitter.TwitterLineItemCloneApi import TwitterLineItemCloneApi
from restapi.views.device_id import device_id
from restapi.views.stats_proxy import proxy_to
from restapi.views.audience_proxy import audience_proxy, advertiser_stats_proxy
from restapi.views.Reports import Reports
from restapi.views.NoBidReports import NoBidReports
from restapi.views.TWReports import TWReports
from restapi.views.Schema import Schema, Perm

from restapi.views.AdPreviewApi import AdPreviewApi

from restapi.views.HttpCacheControl import HttpCacheDrop

# Routers provide an easy way of automatically determining the URL conf.
# router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [  # pylint: disable=invalid-name
    url(r'^campaigns$', CampaignList.as_view(), {'http_caching': True}),
    url(r'^campaigns/twitter$', TWCampaignList.as_view()),

    # This end point gets all campaigns associated with a provided campaign ID
    url(r'^campaigns/(?P<pk>[0-9]+)$', CampaignDetail.as_view(), {'http_caching': True}),
    url(r'^campaigns/twitter/(?P<pk>[0-9]+)$', TWCampaignDetail.as_view()),
    url(r'^campaigns/bulk', CampaignBulk.as_view()),

    url(r'^currencies$', CurrencyList.as_view()),
    url(r'^currencies/(?P<pk>[0-9]+)$', CurrencyDetail.as_view()),

    url(r'^account_managers$', AccountManagerList.as_view()),
    url(r'^account_managers/(?P<pk>[0-9]+)$', AccountManagerDetail.as_view()),

    url(r'^agencies$', AgencyList.as_view(), {'http_caching': True}),
    url(r'^agencies/(?P<pk>[0-9]+)$', AgencyDetail.as_view(), {'http_caching': True}),

    url(r'^advertisers$', AdvertiserList.as_view(), {'http_caching': True}),
    # This end point gets all advertisers associated with a provided advertiser ID
    url(r'^advertisers/(?P<pk>[0-9]+)$', AdvertiserDetail.as_view(), {'http_caching': True}),
    url(r'^advertisers/bulk', AdvertiserBulk.as_view()),

    # This end point gets all io's associated with a provided io ID
    url(r'^ios$', IoList.as_view(), {'http_caching': True}),
    url(r'^ios/(?P<pk>[0-9]+)$', IoDetail.as_view(), {'http_caching': True}),

    url(r'^ad_groups$', AdGroupList.as_view(), {'http_caching': True}),
    # This end point gets all ad groups associated with a provided ad group ID
    url(r'^ad_groups/(?P<pk>[0-9]+)$', AdGroupDetail.as_view(), {'http_caching': True}),
    url(r'^ad_groups/change_status$', AdGroupsChangeStatus.as_view()),
    url(r'^ad_groups/replicate$', AdGroupsReplicate.as_view()),
    url(r'^ad_groups/bulk', AdGroupBulk.as_view()),
    url(r'^ad_groups/import/(?P<campaign_id>[0-9]+)$', AdGroupsImport.as_view()),

    url(r'^ads$', AdList.as_view(), {'http_caching': True}),
    # This end point gets all ads associated with a provided ad ID
    url(r'^ads/(?P<pk>[0-9]+)$', AdDetail.as_view(), {'http_caching': True}),
    url(r'^ads/pruning_recommendations/?$', AdPruningRecommendation.AdPruningRecommendation.as_view()),
    url(r'^ads/bulk', AdBulk.as_view()),
    url(r'^ads/replicate', AdsReplicate.as_view()),
    url(r'^ads/change_status', AdsChangeStatus.as_view()),
    url(r'^ads/resubmit', AdsResubmit.as_view()),
    url(r'^ads/disapproved', AdDisapproved.as_view()),

    url(r'^mraid_ads_templates$', MraidAdTemplateList.as_view()),
    url(r'^mraid_ads_templates/(?P<pk>[0-9]+)$', MraidAdTemplateDetail.as_view()),

    url(r'^audit_logs$', AuditLogList.as_view(), {'http_caching': True}),
    url(r'^audit_logs/(?P<pk>[0-9]+)$', AuditLogDetail.as_view(), {'http_caching': True}),

    url(r'^events$', EventList.as_view(), {'http_caching': True}),
    url(r'^events/(?P<pk>[0-9]+)$', EventDetail.as_view(), {'http_caching': True}),

    url(r'^init$', InitList.as_view(), {'http_caching': True}),

    #    url(r'^revmaps$', RevmapList.as_view()),
    #    url(r'^revmaps/(?P<ad_group_id>[0-9]+)$', RevmapDetail.as_view()),
    url(r'^revmaps/update_all$', RevmapsUpdateAll.as_view()),

    url(r'^blobs$', Blobs.as_view()),

    url(r'^transcoding$', Transcoding.as_view()),
    url(r'^transcoding/(?P<job_id>.+)$', Transcoding.as_view()),

    url(r'^search_live$', SearchLive.as_view(), {'http_caching': True}),
    url(r'^search$', Search.as_view(), {'http_caching': True}),

    url(r'^bidder_black_lists$', BidderBlacklistList.as_view()),
    url(r'^bidder_black_lists/(?P<pk>[0-9]+)$', BidderBlacklistDetail.as_view()),

    url(r'^bidder_white_lists$', BidderWhitelistList.as_view()),
    url(r'^bidder_white_lists/(?P<pk>[0-9]+)$', BidderWhitelistDetail.as_view()),

    url(r'^custom_hints$', CustomHintList.as_view()),
    url(r'^custom_hints/(?P<pk>[0-9]+)$', CustomHintDetail.as_view()),

    url(r'^bidder_black_lists/delete$', BidderBlacklistDelete.as_view()),
    url(r'^bidder_white_lists/delete$', BidderWhitelistDelete.as_view()),
    url(r'^custom_hints/delete$', CustomHintDelete.as_view()),
    url(r'^discrete_pricings/delete$', DiscretePricingDelete.as_view()),

    url(r'^bidder_black_lists/bulk$', BidderBlacklistBulk.as_view()),
    url(r'^bidder_white_lists/bulk$', BidderWhitelistBulk.as_view()),
    url(r'^custom_hints/bulk$', CustomHintBulk.as_view()),
    url(r'^discrete_pricings/bulk$', DiscretePricingBulk.as_view()),

    url(r'^discrete_pricings$', DiscretePricingList.as_view()),
    url(r'^discrete_pricings/(?P<pk>[0-9]+)$', DiscretePricingDetail.as_view()),

    # url(r'^users$', ManageUserList.as_view()),
    # url(r'^users/(?P<pk>[0-9]+)$', ManageUserDetail.as_view()),

    url(r'^auth_users$', UserList.as_view(), {'http_caching': True}),
    url(r'^auth_users/(?P<pk>[0-9]+)$', UserDetail.as_view(), {'http_caching': True}),
    url(r'^set_password/(?P<token>[0-9a-f]+)/(?P<username>.+)$', UserSetPassword.as_view()),

    url(r'^stats_api/(?P<path>.*)$', proxy_to, {'target_url': 'https://api.manage.com/3/'}),
    url(r'^audience_api/(?P<path>.*)$', audience_proxy),
    url(r'^advertiser_stats_api/(?P<token>.*)/(?P<path>.*)$', advertiser_stats_proxy),

    url(r'^get_config$', ConfigView.as_view()),

    url(r'^reports/(?P<path>.*)$', Reports.as_view()),
    url(r'^no_bid_reports/(?P<path>.*)$', NoBidReports.as_view()),
    url(r'^tw_reports/(?P<path>.*)$', TWReports.as_view()),

    url(r'^bidder_insight$', BidderInsight.as_view()),

    url(r'^device_id$', device_id),

    url(r'^trading_desks$', TradingDeskList.as_view(), {'http_caching': True}),
    url(r'^trading_desks/(?P<pk>[0-9]+)$', TradingDeskDetail.as_view(), {'http_caching': True}),

    url(r'^schema$', Schema.as_view(), {'http_caching': True}),
    url(r'^perm/?$', Perm.as_view(), {'http_caching': True}),

    # Twitter API
    url(r'^twitter_user$', TwitterUserList.as_view()),
    url(r'^twitter_user/(?P<pk>[0-9]+)$', TwitterUserDetail.as_view()),
    url(r'^twitter_user/search', TwitterUserSearchApi.as_view()),
    url(r'^twitter_user/verify', TwitterUsersVerifyApi.as_view()),
    url(r'^twitter_account$', TwitterAccountList.as_view()),
    url(r'^twitter_account/live_list$', TwitterLiveAccountsApi.as_view()),
    url(r'^twitter_account/(?P<pk>[0-9]+)$', TwitterAccountDetail.as_view()),
    url(r'^twitter_account/(?P<pk>[0-9]+)$', TwitterAccountDelete.as_view()),
    url(r'^twitter_account/add', TwitterAddAccountApi.as_view()),
    url(r'^twitter_sync$', TwitterSyncApi.as_view()),

    url(r'^twitter_campaign$', TwitterCampaignList.as_view()),
    url(r'^twitter_campaign/(?P<pk>[0-9]+)$', TwitterCampaignDetail.as_view()),

    url(r'^twitter_campaign/generate$', TwitterCampaignGenerateApi.as_view()),
    url(r'^twitter_campaign/validate$', TwitterCampaignValidateApi.as_view()),

    url(r'^twitter_line_item$', TwitterLineItemList.as_view()),
    url(r'^twitter_line_item/(?P<pk>[0-9]+)$', TwitterLineItemDetail.as_view()),
    url(r'^twitter_line_item/check$', TwitterLineItemApi.as_view()),
    url(r'^twitter_line_item/bulk$', TwitterLineItemBulk.as_view()),
    url(r'^twitter_targeting$', TwitterTargetingListView.as_view()),
    url(r'^twitter_targeting/(?P<pk>[0-9]+)$', TwitterTargetingDetail.as_view()),

    url(r'^twitter_targeting/user_interests$', TwitterUserInterestListView.as_view()),
    url(r'^twitter_targeting/devices', TwitterDeviceListView.as_view()),
    url(r'^twitter_targeting/app_store_categories', TwitterAppCategoryListView.as_view()),
    url(r'^twitter_targeting/user_interests$', TwitterUserInterestListView.as_view()),
    url(r'^twitter_targeting/locations', TwitterLocationListView.as_view()),
    url(r'^twitter_targeting/os_versions', TwitterOsVersionListView.as_view()),

    url(r'^twitter_targeting/carriers', TwitterCarrierListView.as_view()),
    url(r'^twitter_targeting/tv_markets', TwitterTVMarketListView.as_view()),
    url(r'^twitter_targeting/tv_genres', TwitterTVGenreListView.as_view()),
    url(r'^twitter_targeting/events', TwitterEventListView.as_view()),

    url(r'^twitter_promoted_tweet$', TwitterPromotedTweetList.as_view()),
    url(r'^twitter_promoted_tweet/(?P<pk>[0-9]+)$', TwitterPromotedTweetDetail.as_view()),
    url(r'^twitter_promoted_tweet/fetch$', TwitterPromotedTweetApi.as_view()),
    url(r'^twitter_promoted_user$', TwitterPromotableUserApi.as_view()),
    
    url(r'^twitter_tweet$', TwitterTweetList.as_view()),
    url(r'^twitter_tweet/(?P<pk>[0-9]+)$', TwitterTweetDetail.as_view()),

    url(r'^twitter_app_card$', TwitterAppCardList.as_view()),
    url(r'^twitter_app_card/(?P<pk>[0-9]+)$', TwitterAppCardDetail.as_view()),

    url(r'^twitter_app_list$', TwitterAccountAppList.as_view()),
    url(r'^twitter_funding_instrument$', TwitterFundingInstrumentListView.as_view()),
    url(r'^twitter_funding_instrument/fetch$', TwitterFundingInstrumentApi.as_view()),
    url(r'^twitter_web_event_tags/fetch$', TwitterWebEventTagApi.as_view()),

    url(r'^twitter_revmap$', TwitterRevmapList.as_view()),
    url(r'^twitter_revmap/(?P<campaign_id>[0-9]+)$', TwitterRevmapDetail.as_view()),

    url(r'^twitter_tailored_audience$', TwitterTailoredAudienceList.as_view()),
    url(r'^twitter_tailored_audience/(?P<pk>[0-9]+)$', TwitterTailoredAudienceDetail.as_view()),

    url(r'^twitter/oauth/advertiser', RawAdvertiserList.as_view()),
    url(r'^twitter/oauth/sign_url', TwitterAccessTokenApi.as_view()),
    url(r'^twitter/oauth/callback', TWitterCallbackApi.as_view()),
    url(r'^twitter/oauth/tw_account', RawTwitterAccountList.as_view()),
    url(r'^twitter/file_get', TwitterFileDownloadApi.as_view()),

    url(r'^twitter/keyword_recommendation', TwitterKeywordRecommendationApi.as_view()),
    url(r'^twitter/handle_recommendation', TwitterHandleRecommendationApi.as_view()),
    url(r'^twitter/reach_estimate', TwitterReachEstimateApi.as_view()),
    url(r'^twitter/tv/shows', TwitterTVShowApi.as_view()),
    url(r'^twitter/tv/genres', TwitterTVGenreListView.as_view()),
    url(r'^twitter/tv/channels', TwitterTVChannelListView.as_view()),
    url(r'^twitter/behavior_taxonomies', TwitterBehaviorTaxonomyListView.as_view()),
    url(r'^twitter/behaviors', TwitterBehaviorListView.as_view()),
    url(r'^twitter/behavior_full_list', TwitterBehaviorJSONListView.as_view()),

    url(r'^tw_clone/twitter_line_items', TwitterLineItemCloneApi.as_view()),

    url(r'^drop_cache/(?P<model_name>[a-zA-Z_]+)$', HttpCacheDrop.as_view()),
    url(r'^drop_cache/(?P<model_name>[a-zA-Z_]+)/(?P<pks>[0-9,]+)$', HttpCacheDrop.as_view()),

    url(r'^ad_preview$', AdPreviewApi.as_view()),

    url(r'^auth/login/?$', 'restapi.views.login.login', name='login'),
    url(r'^auth/logout/?$', 'restapi.views.logout.logout', name='logout'),

    url(r'auth/password/reset/?$', 'restapi.views.password_reset.password_reset', name='password_reset'),
    url(r'auth/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/?$',
        'restapi.views.password_reset.password_reset_confirm', name='password_reset_confirm'),
]

urlpatterns += [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

urlpatterns = format_suffix_patterns(urlpatterns)  # pylint: disable=invalid-name
