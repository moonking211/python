# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import json
import re
import sys
import string
from datetime import datetime
from optparse import make_option
from django.conf import settings
from django.db import connection
from django.core.management.base import BaseCommand, CommandError
from django.utils.http import int_to_base36, base36_to_int
from restapi.email import send_twitter_alert_email, send_twitter_sync_error_email, send_twitter_email
from restapi.models.managers import BaseManager
from restapi.models.choices import STATUS_CHOICES, STATUS_ENABLED, STATUS_PAUSED, STATUS_ARCHIVED
from restapi.models.Campaign import Campaign
from restapi.models.twitter.TwitterConfig import TW_TARGETING_TYPE
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.models.twitter.TwitterUser import TwitterUser
from restapi.models.twitter.TwitterCampaign import TwitterCampaign
from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
from restapi.models.twitter.TwitterAppCard import TwitterAppCard
from restapi.models.twitter.TwitterTweet import TwitterTweet
from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.models.twitter.TwitterTailoredAudience import TwitterTailoredAudience
from restapi.models.twitter.TwitterTargetingModels import *
from restapi.models.twitter.TwitterTVTargeting import *
from restapi.models.twitter.TwitterBehaviorTargeting import *

class Command(BaseCommand):
    help = 'Syncs Twitter Account Data'
    dryrun = False
    verbose = False
    sync_errors = {}

    SYNC_ERROR_CODES = {
        '100': 'Cannot find matching Manage Campaign from Twitter Campaign',
        '101': 'Twitter Campaign Advertiser does not match Manage Campaign Advertiser'
    }

    option_list = BaseCommand.option_list  + (
                        make_option('--tw_account_id', action='store',
                            dest='tw_account_id',
                            default='',
                            help='Twitter Account ID'),
                        make_option('--tw_campaign_id', action='store',
                            dest='tw_campaign_id',
                            default='',
                            help='Twitter Campaign ID'),
                        make_option('--campaign_id', action='store',
                            dest='campaign_id',
                            default='',
                            help='Manage Campaign ID'),
                        make_option('--targeting', action='store',
                            dest='targeting',
                            default='',
                            help='Twitter Targeting'),
                        make_option('--dryrun', action='store_true',
                            dest='dryrun',
                            default=False,
                            help='Sync Dry Run'),
                        make_option('--v', action='store_true',
                            dest='verbose',
                            default=False,
                            help='Verbose'),
                        )


    def handle(self, *args, **options):
        manage_campaign_id = None
        tw_campaign_id = None
        tw_account_id = None

        if 'tw_account_id' in options:
            tw_account_id = options['tw_account_id']

        if 'tw_campaign_id' in options:
            tw_campaign_id = options['tw_campaign_id']

        if 'campaign_id' in options:
            manage_campaign_id = options['campaign_id']

        if 'targeting' in options:
            targeting = options['targeting']

        if 'dryrun' in options and options['dryrun'] is True:
            self.dryrun = True

        if 'verbose' in options and options['verbose'] is True:
            self.verbose = True

        if targeting != '' and targeting is not None:
            if targeting == 'location' or targeting == 'all':
                self._twitter_sync_location_country()
            if targeting == 'app_category' or targeting == 'all':
                self._twitter_sync_app_category()
            if targeting == 'carrier' or targeting == 'all':
                self._twitter_sync_carrier()
            if targeting == 'device' or targeting == 'all':
                self._twitter_sync_device()
            if targeting == 'user_interest' or targeting == 'all':
                self._twitter_sync_user_interest()
            if targeting == 'os_version' or targeting == 'all':
                self._twitter_sync_os_version()
            if targeting == 'tv' or targeting == 'all':
                self._twitter_sync_tv()
            if targeting == 'behavior' or targeting == 'all':
                self._twitter_sync_behavior()

        else:
            self._twitter_sync_account(dict(manage_campaign_id=manage_campaign_id, tw_account_id=tw_account_id, tw_campaign_id=tw_campaign_id))


    def _twitter_sync_location_country(self):
        m_account = TwitterAccount.objects_raw.first()
        api_countries_data = TwitterLocation.fetch_countries(dict(account_id=m_account.tw_account_id))
        api_countries = api_countries_data['data']
        for api_country in api_countries:
            try:
                print "Syncing Country: " + api_country['name'] + " (" + api_country['targeting_value'] + ")"
                m_tw_location = TwitterLocation.objects_raw.get(location_name=api_country['name'])
                m_tw_location.tw_targeting_id = api_country['targeting_value']
                m_tw_location.save_raw()

            except TwitterLocation.DoesNotExist:
                print "------> Cannot find Country Targeting: " + api_country['name']


    def _twitter_sync_behavior(self):
        self._twitter_sync_behavior_taxonomies()
        self._twitter_sync_behavior_by_country('US')
        self._twitter_sync_behavior_by_country('GB')


    def _twitter_sync_behavior_taxonomies(self):
        m_account = TwitterAccount.objects_raw.first()
        api_taxonomies = TwitterBehaviorTaxonomy.fetch_behavior_taxonomies(dict(account_id=m_account.tw_account_id)).get('data', [])
        for api_taxonomy in api_taxonomies:
            api_taxonomy['id'] = base36_to_int(api_taxonomy['id'])
            if api_taxonomy.get('parent_id'):
                api_taxonomy['parent_id'] = base36_to_int(api_taxonomy['parent_id'])
            else:
                api_taxonomy['parent_id'] = None

            print "Syncing Behavior Taxonomy: %s (%s)" % (api_taxonomy['name'], api_taxonomy['id'])
            behavior_taxonomy, created = TwitterBehaviorTaxonomy.objects_raw.get_or_create(tw_behavior_taxonomy_id=api_taxonomy['id'],
                                                              parent_id=api_taxonomy['parent_id'])
            behavior_taxonomy.name = api_taxonomy['name']
            behavior_taxonomy.save()


    def _twitter_sync_behavior_by_country(self, country_code):
        m_account = TwitterAccount.objects_raw.first()
        api_behaviors = TwitterBehavior.fetch_behaviors(dict(account_id=m_account.tw_account_id, country_code=country_code)).get('data', [])
        for api_behavior in api_behaviors:
            api_behavior['id'] = base36_to_int(api_behavior['id'])
            api_behavior['behavior_taxonomy_id'] = base36_to_int(api_behavior['behavior_taxonomy_id'])
            print "Syncing Behavior: %s (%s) %s" % (api_behavior['name'], api_behavior['id'],
                                                    api_behavior['country_code'])
            behavior, created = TwitterBehavior.objects_raw.get_or_create(tw_targeting_id=api_behavior['id'],
                                                      tw_behavior_taxonomy_id=api_behavior['behavior_taxonomy_id'],
                                                      partner_source=api_behavior['partner_source'],
                                                      country_code=api_behavior['country_code'])
            behavior.name = api_behavior['name']
            behavior.audience_size = api_behavior['audience_size']
            behavior.save()
            taxonomy = behavior.tw_behavior_taxonomy

            setattr(taxonomy, country_code, True)
            taxonomy.save()
            if taxonomy.parent:
                setattr(taxonomy.parent, country_code, True)
                taxonomy.parent.save()


    def _twitter_sync_tv(self):
        self._twitter_sync_tv_market()
        self._twitter_sync_tv_genre()


    def _twitter_sync_tv_genre(self):
        m_account = TwitterAccount.objects_raw.first()
        api_tv_genres_data = TwitterTVGenre.fetch_tv_genres(dict(account_id=m_account.tw_account_id)).get('data', [])
        for api_tv_genre in api_tv_genres_data:
            print "Syncing TV Genre: %s (%s)" % (api_tv_genre['name'], api_tv_genre['id'])
            tv_genre, created = TwitterTVGenre.objects_raw.get_or_create(tw_targeting_id=api_tv_genre['id'])
            tv_genre.name = api_tv_genre['name']
            tv_genre.save()

    def _twitter_sync_tv_market(self):
        m_account = TwitterAccount.objects_raw.first()
        api_tv_markets_data = TwitterTVMarket.fetch_tv_markets(dict(account_id=m_account.tw_account_id)).get('data', [])
        for api_tv_market in api_tv_markets_data:
            api_tv_market['id'] = base36_to_int(api_tv_market['id'])
            print "Syncing TV Market: %s (%s)" % (api_tv_market['name'], api_tv_market['id'])
            tv_market, created = TwitterTVMarket.objects_raw.get_or_create(tw_tv_market_id=api_tv_market['id'],
                                                      country_code=api_tv_market['country_code'],
                                                      locale=api_tv_market['locale'])
            tv_market.name = api_tv_market['name']
            tv_market.save()
            tv_channels_data=TwitterTVChannel.fetch_tv_genres(dict(tw_tv_market_id=api_tv_market['id'])).get('data', [])
            for api_tv_channel in tv_channels_data:
                print "Syncing TV Channel: %s (%s)" % (api_tv_channel['name'], api_tv_channel['id'])
                tv_channel, created = TwitterTVChannel.objects_raw.get_or_create(tw_targeting_id=api_tv_channel['id'])
                tv_channel.name = api_tv_channel['name']
                tv_channel.tv_markets.add(tv_market)
                tv_channel.save()


    def _twitter_sync_os_version(self):
        m_account = TwitterAccount.objects_raw.first()
        api_os_versions_data = TwitterOsVersion.fetch_os_versions(dict(account_id=m_account.tw_account_id))
        api_os_versions = api_os_versions_data['data']
        for api_os_version in api_os_versions:
            try:
                print "Syncing OS Version: " + api_os_version['platform'] + " " + api_os_version['name'] + " (" + api_os_version['number'] + ")"
                m_tw_os_version = TwitterOsVersion.objects_raw.get(platform=api_os_version['platform'], tw_targeting_id=base36_to_int(api_os_version['targeting_value']))
                m_tw_os_version.number = api_os_version['number']

            except TwitterOsVersion.DoesNotExist:
                print "------> Adding OS Version: " + api_os_version['platform'] + " " + api_os_version['name'] + " (" + api_os_version['number'] + ")"
                m_tw_os_version = TwitterOsVersion(platform=api_os_version['platform'], tw_targeting_id=base36_to_int(api_os_version['targeting_value']), os_version=api_os_version['name'], number=api_os_version['number'])
            m_tw_os_version.save_raw()


    def _twitter_sync_app_category(self):
        m_account = TwitterAccount.objects_raw.first()
        api_app_categories_data = TwitterAppCategory.fetch_app_categories(dict(account_id=m_account.tw_account_id))
        api_app_categories = api_app_categories_data['data']
        for api_app_category in api_app_categories:
            if api_app_category['os_type'] == 'ANDROID':
                os = 'Android'
            elif api_app_category['os_type'] == 'IOS':
                os = 'iOS'
            try:
                print "Syncing App Category: " + api_app_category['name'] + " (" + api_app_category['targeting_value'] + ")"
                m_tw_app_category = TwitterAppCategory.objects_raw.get(platform=os, app_category=api_app_category['name'])

            except TwitterAppCategory.DoesNotExist:
                print "------> Adding App Category Targeting: " + api_ap_category['name']
                m_tw_app_category = TwitterAppCategory(tw_targeting_id=base36_to_int(api_app_category['targeting_value']), platform=api_app_category['platform'], api_app_category=api_os_version['name'], number=api_os_version['number'])

            m_tw_app_category.save_raw()


    def _twitter_sync_carrier(self):
        m_account = TwitterAccount.objects_raw.first()
        api_carriers_data = TwitterCarrier.fetch_carriers(dict(account_id=m_account.tw_account_id))
        api_carriers = api_carriers_data['data']
        for api_carrier in api_carriers:
            try:
                print "Syncing Carrier: " + api_carrier['name'] + " (" + api_carrier['country_code'] + ") => " + api_carrier['targeting_value']
                m_tw_carrier = TwitterCarrier.objects_raw.get(country_code=api_carrier['country_code'], carrier_name=api_carrier['name'])

            except TwitterCarrier.DoesNotExist:
                print "------> Adding Carrier Targeting: " + api_carrier['name']
                m_tw_carrier = TwitterCarrier(tw_targeting_id=base36_to_int(api_carrier['targeting_value']), country_code=api_carrier['country_code'], carrier_name=api_carrier['name'])

            m_tw_carrier.save_raw()


    def _twitter_sync_device(self):
        m_account = TwitterAccount.objects_raw.first()
        api_devices_data = TwitterDevice.fetch_devices(dict(account_id=m_account.tw_account_id))
        api_devices = api_devices_data['data']
        for api_device in api_devices:
            try:
                print "Syncing Device: " + api_device['name'] + " (" + api_device['platform'] + ") => " + api_device['targeting_value']
                m_tw_device = TwitterDevice.objects_raw.get(platform=api_device['platform'], device=api_device['name'])

            except TwitterDevice.DoesNotExist:
                print "------> Adding Device Targeting: " + api_device['name']
                m_tw_device = TwitterDevice(tw_targeting_id=base36_to_int(api_device['targeting_value']), platform=api_device['platform'], device=api_device['name'])

            m_tw_device.save_raw()


    def _twitter_sync_user_interest(self):
        m_account = TwitterAccount.objects_raw.first()
        api_user_interests_data = TwitterUserInterest.fetch_user_interests(dict(account_id=m_account.tw_account_id))
        api_user_interests = api_user_interests_data['data']
        for api_user_interest in api_user_interests:
            try:
                print "Syncing User Interest: " + api_user_interest['name']
                category, subcategory = api_user_interest['name'].split("/")
                m_tw_user_interest = TwitterUserInterest.objects_raw.get(category=category, subcategory=subcategory)

            except TwitterUserInterest.DoesNotExist:
                print "------> Adding User Interest: " + api_user_interest['name']
                m_tw_user_interest = TwitterUserInterest(tw_targeting_id=base36_to_int(api_user_interest['targeting_value']), category=category, subcategory=subcategory)

            m_tw_user_interest.save_raw()


    def _check_api_errors(self, data, account, class_name="Twitter"):
        if 'errors' in data and data['errors']:
            if self.verbose:
                print "API ERROR: Twitter "+  class_name + ": " + json.dumps({account.tw_account_id: {class_name: data['errors']}})
            self._insert_sync_error(data, account, class_name)
            return data['errors']
        return False


    def _insert_sync_error(self, data, account, class_name="Twitter"):
        if (account, class_name) not in self.sync_errors:
            self.sync_errors[(account, class_name)] = []
        self.sync_errors[(account, class_name)].append(data['errors'])

    def _twitter_sync_account(self, args):
        start_time = datetime.now()
        settings.SYSTEM_USER = True
        manage_campaign_cache = {}
        if self.verbose:
            print "Syncing Twitter Data"
        # Fetch all twitter accounts
        os_platform = None;
        if 'tw_account_id' in args and args['tw_account_id']:
            account_id = args['tw_account_id']
            if isinstance(account_id, basestring) and not account_id.isdigit():
                account_id = base36_to_int(account_id)
            m_accounts = []
            try:
                account = TwitterAccount.objects_raw.get(tw_account_id=account_id)
                m_accounts.append(account)
            except TwitterAccount.DoesNotExist:
                print "Cannot find account: " + str(account_id)
        else:
            m_accounts = TwitterAccount.objects_raw.all()

        data = {}
        for m_account in m_accounts:
            try:
                oauth_token = None
                oauth_secret = None
                try:
                    oauth_token = m_account.tw_twitter_user_id.oauth_token
                    oauth_secret = m_account.tw_twitter_user_id.oauth_secret
                except TwitterUser.DoesNotExist:
                    oauth_token = None
                    oauth_secret = None
                    pass
                if oauth_token == '':
                    oauth_token = None
                if oauth_secret == '':
                    oauth_secret = None

                # Check status of each Twitter Account via API
                api_accounts_data = TwitterAccount.fetch_accounts(dict(account_id=m_account.tw_account_id))

                self._check_api_errors(api_accounts_data, m_account, "TwitterAccount")

                api_accounts = []
                if isinstance(api_accounts_data['data'], dict):
                    api_accounts.append(api_accounts_data['data'])
                elif isinstance(api_accounts_data['data'], (list, tuple)):
                    api_accounts = api_accounts_data['data']

                if self.verbose:
                    print "--> Fetching Account data for: " + str(m_account.tw_account_id) + " (" + str(int_to_base36(m_account.tw_account_id)) + ")"
            except KeyError:
                pass

            for api_account in api_accounts:
                # Fetch campaigns from Twitter
                try:
                    if 'manage_campaign_id' in args and args['manage_campaign_id'] is not None:
                        manage_campaign_id = args['manage_campaign_id']
                        if oauth_token is not None and oauth_secret is not None:
                            api_campaigns_data = TwitterCampaign.fetch_campaigns(dict(account_id=m_account.tw_account_id, campaign_id=manage_campaign_id), True, oauth_token, oauth_secret)
                        else:
                            api_campaigns_data = TwitterCampaign.fetch_campaigns(dict(account_id=m_account.tw_account_id, campaign_id=manage_campaign_id), True)
                    else:
                        if oauth_token is not None and oauth_secret is not None:
                            api_campaigns_data = TwitterCampaign.fetch_campaigns(dict(account_id=m_account.tw_account_id), True, oauth_token, oauth_secret)
                        else:
                            api_campaigns_data = TwitterCampaign.fetch_campaigns(dict(account_id=m_account.tw_account_id), True)

                    self._check_api_errors(api_campaigns_data, m_account, "TwitterCampaign")

                    api_campaigns = []
                    if isinstance(api_campaigns_data['data'], dict):
                        api_campaigns.append(api_campaigns_data['data'])
                    elif isinstance(api_campaigns_data['data'], (list, tuple)):
                        api_campaigns = api_campaigns_data['data']

                    if 'os_platform' in  api_campaigns_data:
                        os_platform = api_campaigns_data['os_platform']

                    if self.verbose:
                        print "--> Fetching App Cards for: " + str(m_account.tw_account_id)

                    api_campaign_app_cards_data = TwitterAppCard.fetch_app_cards(dict(account_id=m_account.tw_account_id), True, oauth_token, oauth_secret)

                    self._check_api_errors(api_campaign_app_cards_data, m_account, "TwitterAppCard")

                    api_campaign_app_cards = []
                    if isinstance(api_campaign_app_cards_data['data'], dict):
                        api_campaign_app_cards.append(api_campaign_app_cards_data['data'])
                    elif isinstance(api_campaign_app_cards_data['data'], (list, tuple)):
                        api_campaign_app_cards = api_campaign_app_cards_data['data']

                    for api_campaign_app_card in api_campaign_app_cards:
                        if self.verbose:
                            print "----> Syncing App Card: " + str(api_campaign_app_card['name']) + " (" + str(api_campaign_app_card['card_type']) + ")"

                    if self.verbose:
                        print "--> Fetching Tailored Audiences for: " + str(m_account.tw_account_id)

                    api_tailored_audiences_data = TwitterTailoredAudience.fetch_tailored_audience(dict(account_id=m_account.tw_account_id), True, oauth_token, oauth_secret)

                    api_tailored_audiences = []
                    if isinstance(api_tailored_audiences_data['data'], dict):
                        api_tailored_audiences.append(api_tailored_audiences_data['data'])
                    elif isinstance(api_tailored_audiences_data['data'], (list, tuple)):
                        api_tailored_audiences = api_tailored_audiences_data['data']

                    for api_tailored_audience in api_tailored_audiences:
                        if self.verbose:
                            print "----> Syncing Tailored Audience: " + str(api_tailored_audience['name'])

                    if self.verbose:
                        print "--> ("+ str(len(api_campaigns)) + ") total Campaigns"

                except KeyError:
                    pass

                for api_campaign in api_campaigns:
                    api_line_items = []
                    try:
                        campaign_id_int = base36_to_int(api_campaign['id'])

                        if 'tw_campaign_id' in args and args['tw_campaign_id'] is not None and args['tw_campaign_id'] != '':
                            if args['tw_campaign_id'] != str(campaign_id_int):
                                continue

                        if self.verbose:
                            print "--> Syncing Campaign: " + str(api_campaign['name']) + " - (" + str(api_campaign['id']) + ")"

                        campaign_id_int = base36_to_int(api_campaign['id'])

                        # Get Line Items
                        api_line_items_data = TwitterLineItem.fetch_line_items(dict(account_id=m_account.tw_account_id, campaign_id=api_campaign['id']), True, oauth_token, oauth_secret)

                        if isinstance(api_line_items_data['data'], dict):
                            api_line_items.append(api_line_items_data['data'])
                        elif isinstance(api_line_items_data['data'], (list, tuple)):
                            api_line_items = api_line_items_data['data']

                        # Parse Manage Campaign ID from TW Campaign name
                        manage_campaign_id = None
                        if 'manage_campaign_id' in api_campaign and api_campaign['manage_campaign_id']:
                            manage_campaign_id = api_campaign['manage_campaign_id']

                        # Look up Manage Campaign
                        manage_campaign = None
                        if manage_campaign_id in manage_campaign_cache:
                            manage_campaign = manage_campaign_cache[manage_campaign_id]
                        elif manage_campaign_id is not None:
                            try:
                                manage_campaign = Campaign.objects_raw.filter(campaign_id=manage_campaign_id, source_type=2).first()
                                manage_campaign_cache[manage_campaign_id] = manage_campaign
                            except Campaign.DoesNotExist:
                                manage_campaign = None

                        if manage_campaign is None:
                            if self.verbose:
                                print "----> Error: Cannot find internal Manage Campaign: " + str(api_campaign['name'])

                            # Since advertisers are now granting us access to existing Twitter Campaigns,
                            # the Manage Campaign ID won't exist in the Twitter Campaign Name.
                            # For now, we won't flag these as sync errors.  We will skip for now.
                            # self._insert_sync_error({"errors":{"100": self.SYNC_ERROR_CODES['100'] + " - "+ str(api_campaign['name'])}}, m_account, "ManageCampaign")
                            continue

                        # Twitter Advertiser should match internal Manage Campaign advertiser
                        if m_account.advertiser_id.advertiser_id != manage_campaign.advertiser_id.advertiser_id and api_campaign['deleted'] is not True:
                            sync_error = self.SYNC_ERROR_CODES['101'] + ": TW_CAMPAGIN: {tw_campaign} ({tw_campaign_id}), TW_ADVERTISER: {tw_advertiser} ({tw_advertiser_id}), MANAGE_ADVERTISER: {manage_advertiser} ({manage_advertiser_id})." \
                            .format(tw_campaign=str(api_campaign['name']), tw_campaign_id=str(base36_to_int(api_campaign['id'])), \
                                tw_advertiser=str(m_account.advertiser_id), tw_advertiser_id=str(m_account.advertiser_id.advertiser_id), \
                                manage_advertiser=str(manage_campaign.advertiser_id), manage_advertiser_id=str(manage_campaign.advertiser_id.advertiser_id))
                            if self.verbose:
                                print "----> Error: " + sync_error
                            self._insert_sync_error({"errors":{"101": sync_error}}, m_account, "ManageCampaign")
                            continue

                        if self.verbose:
                            print "---> ("+ str(len(api_line_items)) + ") total Line Items"

                    except KeyError:
                        pass

                    for api_line_item in api_line_items:
                        try:
                            if self.verbose:
                                try:
                                    print "----> Syncing Line Item: " + str(api_line_item['name']) + " - (" + str(api_line_item['id']) + ")"
                                except UnicodeEncodeError:
                                    pass
                            line_item_id_int = base36_to_int(api_line_item['id'])

                            api_line_item_targetings_data = TwitterTargeting.fetch_targeting(dict(account_id=m_account.tw_account_id, line_item_id=api_line_item['id']), True, oauth_token, oauth_secret)

                            self._check_api_errors(api_line_item_targetings_data, m_account, "TwitterTargeting")

                            api_line_item_targetings = []
                            if isinstance(api_line_item_targetings_data['data'], dict):
                                api_line_item_targetings.append(api_line_item_targetings_data['data'])
                            elif isinstance(api_line_item_targetings_data['data'], (list, tuple)):
                                api_line_item_targetings = api_line_item_targetings_data['data']

                            for api_line_item_targeting in api_line_item_targetings:
                                if self.verbose:
                                    try:
                                        print "------> Syncing Line Item Targeting: " + str(api_line_item_targeting['name'])
                                    except UnicodeEncodeError:
                                        pass
                            # Line Item Promoted Tweets
                            api_line_item_promoted_tweets_data = TwitterPromotedTweet.fetch_promoted_tweet(dict(account_id=m_account.tw_account_id, line_item_id=api_line_item['id'], os_platform=os_platform), True, oauth_token, oauth_secret)

                            self._check_api_errors(api_line_item_promoted_tweets_data, m_account, "TwitterPromotedTweet")

                            api_line_item_promoted_tweets = []
                            if isinstance(api_line_item_promoted_tweets_data['data'], dict):
                                api_line_item_promoted_tweets.append(api_line_item_promoted_tweets_data['data'])
                            elif isinstance(api_line_item_promoted_tweets_data['data'], (list, tuple)):
                                api_line_item_promoted_tweets = api_line_item_promoted_tweets_data['data']

                            for api_line_item_promoted_tweet in api_line_item_promoted_tweets:
                                if self.verbose:
                                    print "------> Syncing Line Item Promoted Tweet: " + str(api_line_item_promoted_tweet['tweet_id'])

                            # Get Rev Map
                            if self.verbose:
                                print "--> Sync Revmap Manage Campaign: " + str(manage_campaign)

                            if manage_campaign is not None:
                                manage_campaign_rev_map = TwitterRevmap.objects_raw.filter(campaign_id=manage_campaign, tw_campaign_id=0, tw_line_item_id=0).first()
                                if manage_campaign_rev_map is not None:
                                    manage_campaign_opt_type = manage_campaign_rev_map.opt_type
                                    manage_campaign_opt_value = manage_campaign_rev_map.opt_value

                                    tw_campaign_rev_map = None
                                    if manage_campaign_opt_type is not None and manage_campaign_opt_value is not None:
                                        try:
                                            tw_line_item = TwitterLineItem.objects_raw.get(tw_campaign_id=campaign_id_int, tw_line_item_id=line_item_id_int)
                                            if tw_line_item:
                                                tw_campaign_rev_map = TwitterRevmap.objects_raw.get(campaign_id=manage_campaign, tw_campaign_id=tw_line_item.tw_campaign_id, tw_line_item_id=tw_line_item)
                                        except TwitterLineItem.DoesNotExist:
                                            tw_campaign_rev_map = None
                                        except TwitterRevmap.DoesNotExist:
                                            tw_campaign_rev_map = TwitterRevmap(campaign_id=manage_campaign, tw_campaign_id=tw_line_item.tw_campaign_id, tw_line_item_id=tw_line_item)

                                        if tw_campaign_rev_map is not None:
                                            tw_campaign_rev_map.opt_type = manage_campaign_opt_type
                                            tw_campaign_rev_map.opt_value = manage_campaign_opt_value
                                            tw_campaign_rev_map.save_raw();
                            if self.verbose:
                                print "-" * 50
                        except KeyError:
                            pass

                    if self.verbose:
                        print "+" * 100

                # Fetch all Manage Twitter Campaigns owned by Advertiser and sync Manage Campaign status
                manage_campaigns = Campaign.objects_raw.filter(advertiser_id=m_account.advertiser_id, source_type=2)
                for manage_campaign in manage_campaigns:
                    # Find any active Twitter Campaigns
                    tw_campaigns = TwitterCampaign.objects_raw.filter(campaign_id=manage_campaign.campaign_id, status='enabled')
                    if tw_campaigns is not None and manage_campaign.status != 'enabled':
                        manage_campaign.status = 'enabled'
                        manage_campaign.save_raw()
                    elif tw_campaigns is None and manage_campaign.status != 'paused':
                        manage_campaign.status = 'paused'
                        manage_campaign.save_raw()

                    if self.verbose:
                        print  "--> Setting Manage Campaign status - " + str(manage_campaign) + ": " + str(manage_campaign.status)

                if self.verbose:
                    print "*" * 150

        # Return Sync Result
        end_time = datetime.now()
        if self.verbose:
            print 'Sync Script Duration: {}'.format(end_time - start_time)

        if self.sync_errors:
            send_twitter_sync_error_email({"data":json.dumps(self.sync_errors)})
            print {
                'error': True,
                'code': json.dumps(self.sync_errors),
                'message': 'Twitter API Errors'
            }
        else:
            sql = "REPLACE INTO job_status SET job_name='twitter_sync', job_type='twitter', last_finished=NOW(), threshold=120"
            cursor = connection.cursor()
            try:
                cursor.execute(sql)
                if settings.TW_SYNC_ALERT:
                    send_twitter_email('Twitter Sync Success', 'Twitter Sync Success. Script Duration: {}'.format(end_time - start_time));
                print {
                    'error': False,
                    'code': 200,
                    'message': 'OK'
                }
            except:
                print {
                    'error': True,
                    'message': 'Twitter synced but cannot add entry to job_status table'
                }
            finally:
                cursor.close()
