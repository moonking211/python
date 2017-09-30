import itertools
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from restapi.models.twitter.TwitterTargetingModels import *
from django.utils.http import int_to_base36
import twitter
from django.conf import settings
from restapi.models.twitter.TwitterAccount import TwitterAccount
from rest_framework import status
from .helper import human_format

# https://dev.twitter.com/ads/reference/1/get/accounts/%3Aaccount_id/reach_estimate
class TwitterReachEstimateApi(CreateAPIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        # flag to have at least one targeting
        flag = False
        account_id = data.get('account_id')
        if not account_id:
            return Response(dict(error='account_id is required'), status=status.HTTP_400_BAD_REQUEST)
        account = TwitterAccount.objects_raw.filter(pk=data.get('account_id')).first()
        if not account:
            return Response(dict(error='account_id is invalid'), status=status.HTTP_400_BAD_REQUEST)

        oauth_token=account.tw_twitter_user_id.oauth_token
        oauth_secret=account.tw_twitter_user_id.oauth_secret

        account_id = int_to_base36(long(data.get('account_id')))
        product_type = 'PROMOTED_TWEETS'
        objective = data.get('objective')
        
        try:
            bid_amount_local_micro = int(round(float(data.get('bid_amount_default', 0) or 0), 2) * 1000000)
        except:
            return Response(dict(errors='Invalid bid amount..'), status=status.HTTP_400_BAD_REQUEST)
        
        currency = 'USD'
        campaign_daily_budget_amount_local_micro = int(round(float(data.get('daily_budget_amount_local_micro', 0)),2) * 1000000)

        if not bid_amount_local_micro or not campaign_daily_budget_amount_local_micro:
            return Response(dict(error='bid_amount_local_micro or campaign_daily_budget_amount_local_micro is missing'),
                            status=status.HTTP_400_BAD_REQUEST)

        similar_to_followers_of_users = ''

        followers = ','.join([item['text'] for sublist in data.get('handles_group') for item in sublist])
        if followers:
            api = twitter.Api(consumer_key=settings.TW_CONSUMER_KEY,
                                  consumer_secret=settings.TW_CONSUMER_SECRET,
                                  access_token_key=settings.TW_ACCESS_TOKEN,
                                  access_token_secret=settings.TW_ACCESS_SECRET)
            invalid_followers = list(followers.split(',')[:100])
            suggested = []
            ids = []
            follower_objs = api.UsersLookup(screen_name=invalid_followers)
            for u in follower_objs:
                screen_name = u.screen_name
                if screen_name in invalid_followers:
                    invalid_followers.remove(screen_name)
                    ids.append(str(u.id))
                else:
                    suggested.append(screen_name)

            similar_to_followers_of_users = ','.join(ids)

        locations = ''
        if data.get('locations_group'):

            for lg in data['locations_group']:
                locations = []
                for l in lg:
                    tw_location = TwitterLocation.objects.get(export_id=l['export_id'])
                    locations.append(tw_location.tw_targeting_id)
                locations = ','.join(locations)

        interests = ','.join([str(item['id']) for sublist in data.get('interests_group') for item in sublist])
        if data['objective'] == 'APP_INSTALLS':
            platforms = '0' if data.get('os') == 'iOS' else '1'
            platform_versions = int_to_base36(data['min_version']['tw_targeting_id']) if data.get('min_version') else ''
            devices = ','.join([int_to_base36(d['tw_targeting_id']) for d in data.get('devices', [])])
        else:
            platforms = ','.join([str(o) for o in data['web_clicks_os']])
            devices = (data['web_click_ios_devices'].split(',') if data['web_click_ios_devices'] else []) + (data['web_click_android_devices'].split(',') if data['web_click_android_devices'] else [])
            versions = []
            if data.get('web_click_ios_min_version'):
                versions.append(int_to_base36(int(data['web_click_ios_min_version'])))
            if data.get('web_click_android_min_version'):
                versions.append(int_to_base36(int(data['web_click_android_min_version'])))
            
            devices = ','.join([int_to_base36(int(d)) for d in devices])
            platform_versions = ','.join(versions)
        
        app_store_categories_expanded = ','.join([int_to_base36(long(item['id'])) for sublist in data.get('app_categories_group') for item in sublist])
        network_operators = ','.join([int_to_base36(d['id']) for d in data.get('carriers', [])])

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token, oauth_secret)
        resource = '/1/accounts/%s/reach_estimate?product_type=%s&' \
                   'objective=%s&' \
                   'bid_amount_local_micro=%s&' \
                   'currency=%s&' \
                   'campaign_daily_budget_amount_local_micro=%s&' \
                   'bid_type=MAX' % (account_id, product_type, objective, bid_amount_local_micro,
                                                         currency, campaign_daily_budget_amount_local_micro)

        optional_params = ['similar_to_followers_of_users', 'locations', 'interests', 'platforms', 'platform_versions',
                           'devices', 'network_operators', 'app_store_categories_expanded']
        _locals = locals()
        for param in optional_params:
            if _locals[param]:
                if param != 'platforms' and param != 'locations' and param != 'platform_versions' and \
                                param != 'devices' and param != 'network_operators':
                    flag = True
                resource += '&%s=%s' % (param, _locals[param])

        if flag:
            response = Request(client, 'get', resource).perform()
            res = response.body['data']
            try:
                res['count'] = '%s ~ %s' % (human_format(res['count']['min']), human_format(res['count']['max']))
                res['engagements'] = '%s ~ %s' % (human_format(res['engagements']['min']),
                                                  human_format(res['engagements']['max']))
                res['impressions'] = '%s ~ %s' % (human_format(res['impressions']['min']),
                                                  human_format(res['impressions']['max']))
                res['estimated_daily_spend_local_micro'] = '$%s ~ $%s' % (round(res['estimated_daily_spend_local_micro']['min'] / 1000000.0, 2), round(res['estimated_daily_spend_local_micro']['max'] / 1000000.0, 2))
                res['infinite_bid_count'] = '%s ~ %s' % (human_format(res['infinite_bid_count']['min']),
                                                         human_format(res['infinite_bid_count']['max']))
                return Response(res)
            except:
                return Response(dict(errors='Invalid response!'), status=status.HTTP_400_BAD_REQUEST)    
        else:
            return Response(dict(errors='At least one targeting is required'), status=status.HTTP_400_BAD_REQUEST)
