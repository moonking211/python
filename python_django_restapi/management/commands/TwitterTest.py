import json
import re
import sys
import string
import numpy
from datetime import datetime
from optparse import make_option
from django.conf import settings
from django.db import connection
from django.core.management.base import BaseCommand, CommandError
from django.utils.http import int_to_base36, base36_to_int
from restapi.email import send_twitter_alert_email, send_twitter_sync_error_email
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

        # gq10nzw
        account = TwitterAccount.objects_raw.get(tw_account_id=1011176351)

        oauth_token = account.tw_twitter_user_id.oauth_token
        oauth_secret = account.tw_twitter_user_id.oauth_secret

        # api_campaigns_data = TwitterCampaign.fetch_campaigns(dict(account_id=account.tw_account_id), True)
        # api_campaign_data = api_campaigns_data['data']
        # campaign_data = api_campaign_data[0]

        # new_campaign_data = {}
        # new_campaign_data['name'] = "CREATE API - Image {1201}"
        # new_campaign_data['account_id'] = 1011176351
        # new_campaign_data['funding_instrument_id'] = campaign_data['funding_instrument_id']
        # new_campaign_data['daily_budget_amount_local_micro'] = campaign_data['daily_budget_amount_local_micro']
        # new_campaign_data['paused'] = str(True).lower()
        # new_campaign_data['standard_delivery'] = str(True).lower()
        # new_campaign_data['start_time'] = '2016-08-09T13:45:00Z'

        # print new_campaign_data
        # new_campaign = TwitterCampaign.create_campaign(new_campaign_data, oauth_token, oauth_secret)
        # print "-------- RESULT --------"
        # print new_campaign

        # update_campaign_data = {}
        # update_campaign_data['campaign_id'] = 8148469
        # update_campaign_data['account_id'] = 1011176351
        # update_campaign_data['daily_budget_amount_local_micro'] = campaign_data['daily_budget_amount_local_micro'] * 2

        # #print update_campaign_data
        # update_campaign = TwitterCampaign.update_campaign(update_campaign_data, oauth_token, oauth_secret)
        # print "-------- RESULT --------"
        # print update_campaign

        #############################################
        # Line Item
        #############################################

        # new_line_item_data = {}
        # new_line_item_data['account_id'] = 1011176351
        # new_line_item_data['campaign_id'] = '4uned'
        # new_line_item_data['name'] = 'CREATE API - VAN - LINE_ITEM'
        # new_line_item_data['product_type'] = 'PROMOTED_TWEETS'
        # new_line_item_data['placements'] = 'ALL_ON_TWITTER'
        # new_line_item_data['objective'] = 'APP_INSTALLS'
        # new_line_item_data['bid_amount_local_micro'] = 10000
        # new_line_item_data['automatically_select_bid'] = str(False).lower()
        # new_line_item_data['paused'] = str(True).lower()

        # new_line_item = TwitterLineItem.create_line_item(new_line_item_data, oauth_token, oauth_secret)
        # print "-------- RESULT --------"
        # print new_line_item

        # update_line_item_data = {}
        # update_line_item_data['account_id'] = 1011176351
        # update_line_item_data['campaign_id'] = '4uned'
        # update_line_item_data['line_item_id'] = int_to_base36(9911328)
        # update_line_item_data['bid_amount_local_micro'] = 500000
        # update_line_item_data['automatically_select_bid'] = str(False).lower()
        # update_line_item_data['paused'] = str(False).lower()

        # update_line_item_data2 = {}
        # update_line_item_data2['account_id'] = 1011176351
        # update_line_item_data2['campaign_id'] = '4uned'
        # update_line_item_data2['line_item_id'] = int_to_base36(9939049)
        # update_line_item_data2['bid_amount_local_micro'] = 400000
        # update_line_item_data2['automatically_select_bid'] = str(False).lower()
        # update_line_item_data2['paused'] = str(False).lower()

        # update_line_item = TwitterLineItem.update_line_item(update_line_item_data, oauth_token, oauth_secret)
        # print "-------- RESULT --------"
        # print update_line_item

        # batch = []
        # batch.append(update_line_item_data)
        # batch.append(update_line_item_data2)

        # bath_update_line_item = TwitterLineItem.batch_update_line_item(batch, 1011176351, '339117672-TI1rfxzoiQdrOHfrPqzbE0FCWkOCcePr9mDDJ4qX', 'ZTSkOFGPXXJqGIWzpgAN7mh3ogg7jxbR1Sc1EPbVL3rDW')
        # print "-------- RESULT --------"
        # print bath_update_line_item

        # m_tw_line_item_targeting = TwitterTargeting.objects_raw.filter(tw_line_item_id=8460210).values()
        # m_tw_line_item_targeting_list = list(m_tw_line_item_targeting)

        # targeting_list = m_tw_line_item_targeting_list

        #print targeting_list

        # new = {
        #     "tw_line_item_id": 8460210,
        #     "tw_targeting_type": 17,
        #     "tw_targeting_id": "3009",
        #     "targeting_value": ""
        # }

        # targeting_list.append(new)
        #print targeting_list
        # batch = []
        # batches = []
        # for x in range(0, len(targeting_list), 20):
        #     batch = targeting_list[x:x+20]
        #     batches.append(batch)

        # print chunks
        # criteria = json.loads(criteria_str)
        # update_targeting = TwitterTargeting.set_targeting(targeting_list, 4503599654958352, oauth_token, oauth_secret)
        # print "=" * 100
        # print json.dumps(update_targeting, indent=4)

        campaign_list = []
        line_item_list = []
        for number in range(3,100):
            print number
            # new_campaign_data = {}
            # new_campaign_data['name'] = "CREATE API - {}".format(number)
            # new_campaign_data['account_id'] = 1011176351
            # new_campaign_data['paused'] = str(True).lower()
            # new_campaign_data['standard_delivery'] = str(True).lower()
            # new_campaign_data['start_time'] = '2016-08-09T13:45:00Z'
            # campaign_list.append(new_campaign_data)
            new_line_item_data = {}
            new_line_item_data['account_id'] = 1011176351
            new_line_item_data['campaign_id'] = 'gq10nz'
            new_line_item_data['name'] ="'CREATE API - LINE_ITEM {}".format(number)
            new_line_item_data['product_type'] = 'PROMOTED_TWEETS'
            new_line_item_data['placements'] = 'ALL_ON_TWITTER'
            new_line_item_data['objective'] = 'APP_INSTALLS'
            new_line_item_data['bid_amount_local_micro'] = 10000
            new_line_item_data['automatically_select_bid'] = str(False).lower()
            new_line_item_data['paused'] = str(True).lower()
            line_item_list.append(new_line_item_data)
        #print line_item_list

        new_line_items = TwitterLineItem.batch_create(line_item_list, 1011176351, oauth_token, oauth_secret)
        print new_line_items
