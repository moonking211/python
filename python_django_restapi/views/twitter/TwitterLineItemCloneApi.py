import traceback
import re
import pytz, json
from datetime import datetime

from django.core import serializers
from django.conf import settings
from django.utils.http import int_to_base36
from django.utils.http import base36_to_int

from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.models.twitter.TwitterCampaign import TwitterCampaign
from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.models.twitter.TwitterTargetingModels import TwitterTargeting, TwitterDevice, TwitterLocation, TwitterOsVersion
from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
from restapi.models.Campaign import Campaign
from restapi.models.twitter.TwitterConfig import TW_TARGETING_ID_TO_ENUM


class TwitterLineItemCloneApi(CreateAPIView):
    permission_classes = (IsAuthenticated, )


    def post(self, request, *args, **kwargs):
        try:
            data = request.DATA
            tw_account_id = data['tw_account_id']
            diff_account = data['different_ads_account']
            create_new_campaign = data['create_new_campaign']
            tweet_ids = data['tweet_ids']
            tw_line_item_ids = data.get('tw_line_item_ids', [])
            objective = data.get('objective')
            daily_budget_amount_local_micro = \
                long(round(float(data.get('daily_budget_amount_local_micro', 0)), 2) \
                * 1000000)
            clone_campaigns = False

            campaigns_daily_budgets = {}
            if data['type'] == 'tw_campaigns_clone':                
                clone_campaigns = True
                tw_line_item_ids = [t.tw_line_item_id \
                    for t in TwitterLineItem.objects.filter(
                        tw_campaign_id__tw_campaign_id__in=data['tw_campaign_ids'])]

            tw_account = TwitterAccount.objects.get(tw_account_id=tw_account_id)
            oauth_token = tw_account.tw_twitter_user_id.oauth_token \
                or settings.TW_ACCESS_TOKEN
            oauth_token_secret = tw_account.tw_twitter_user_id.oauth_secret \
                or settings.TW_ACCESS_SECRET

            tw_campaign_id_to_line_items = {}
            campaign_data = {}
            # active line item count in selected twitter account
            active_line_item_count = TwitterLineItem.objects \
                        .filter(
                            tw_campaign_id__tw_account_id=tw_account,
                            status='enabled') \
                        .count()

            if create_new_campaign:
                # in case we create active line items
                if not data['status'] == 'PAUSED':
                    if active_line_item_count + len(tw_line_item_ids) > 2000:
                        return Response(
                            dict(error="There should be less than 2000 active line" \
                                        " items in one account."),
                            status=status.HTTP_400_BAD_REQUEST)

                def _create_tw_campaign(name):
                    campaign_data['account_id'] = tw_account_id
                    campaign_data['daily_budget_amount_local_micro'] = \
                        daily_budget_amount_local_micro

                    if isinstance(data['funding_instrument_id'],(int,long)):
                        campaign_data['funding_instrument_id'] = \
                            int_to_base36(data['funding_instrument_id'])
                    else:
                        campaign_data['funding_instrument_id'] = \
                            data['funding_instrument_id']

                    campaign_data['name'] = name
                    campaign_data['paused'] = data['status'] == 'PAUSED'
                    campaign_data['start_time'] = data.get(
                        'flight_start_date',
                        datetime.now(pytz.timezone('US/Central')) \
                        .strftime('%Y-%m-%dT%H:%M:%S%z'))
                    campaign_data['end_time'] = data.get('flight_end_date')
                    campaign_data['total_budget_amount_local_micro'] = \
                        long(
                            round(
                                float(data.get('total_budget_amount_local_micro') or 0),
                                2
                            ) * 1000000)

                    campaign_res = TwitterCampaign.create_update_campaign(
                        campaign_data,
                        oauth_token,
                        oauth_token_secret)
                    if not campaign_res['success']:
                        raise Exception(campaign_res.get('error') or campaign_res.get('message'))

                    return campaign_res['data']['id']

                if clone_campaigns:
                    for tw_campaign in TwitterCampaign.objects.filter(tw_campaign_id__in=data['tw_campaign_ids']).all():
                        tw_campaign_id = _create_tw_campaign(
                            "%s{%s}" % (
                                re.sub(r'{.*}', '', tw_campaign.name),
                                data['campaign_id']
                            )
                        )
                        tw_campaign_id_to_line_items[tw_campaign_id] = \
                            TwitterLineItem.objects \
                            .filter(tw_campaign_id=tw_campaign.tw_campaign_id).values()
                else:
                    tw_campaign_id = _create_tw_campaign(
                        "%s {%s}" % (data['campaign'], data['campaign_id'])
                    )

                    tw_campaign_id_to_line_items[tw_campaign_id] = \
                        TwitterLineItem.objects \
                        .filter(tw_line_item_id__in=tw_line_item_ids).values()

            else:
                cloned_active_line_item_count = TwitterLineItem.objects.filter(
                        tw_line_item_id__in=tw_line_item_ids,
                        status='enabled'
                    ).count()
                if (len(data['tw_campaign_ids']) * cloned_active_line_item_count \
                        + active_line_item_count > 2000):
                    return Response(
                            dict(error="There should be less than 200 active line" \
                                        " items in one account."),
                            status=status.HTTP_400_BAD_REQUEST)

                # newly created line item daily budget should be greater than
                # it's campaign daily budget so we need to campaigns' daily 
                # budgets for them
                for tc in TwitterCampaign.objects \
                            .filter(tw_campaign_id__in=data['tw_campaign_ids']):
                    campaigns_daily_budgets[int_to_base36(tc.tw_campaign_id)] = \
                                            tc.daily_budget_amount_local_micro
                
                for campaign_id in data['tw_campaign_ids']:
                    tw_campaign_id_to_line_items[int_to_base36(int(campaign_id))] = \
                        TwitterLineItem.objects \
                        .filter(tw_line_item_id__in=tw_line_item_ids).values()

            # make line item data
            line_items_data = []
            name_to_ids = {}                        
            success_line_item_count = 0
            ignored_line_item_count = 0
            ignored_targetings = []

            for (campaign_id, line_items) in tw_campaign_id_to_line_items.iteritems():
                for item in line_items:
                    item['campaign_id'] = campaign_id
                    if objective:
                        item['objective'] = objective
                        del item['bid_unit']
                        del item['charge_by']
                        del item['optimization']

                    # set line item daily budget to it's campaign's one
                    if create_new_campaign:
                        item['bid_amount_local_micro'] = \
                            min(
                                daily_budget_amount_local_micro, 
                                item['bid_amount_local_micro']
                            )                       
                    else:
                        item['bid_amount_local_micro'] = \
                            min(
                                campaigns_daily_budgets[campaign_id],
                                item['bid_amount_local_micro']
                            )
                    
                    item['placements'] = json.loads(item['placements'])
                    item['categories'] = json.loads(item['categories'])
                    item['tracking_tags'] = json.loads(item['tracking_tags'])

                    item['placements'] = item['placements'] \
                        if item['placements'] else None
                    item['categories'] = item['categories'] \
                        if item['categories'] else None
                    item['tracking_tags'] = item['tracking_tags'] \
                        if item['tracking_tags'] else None

                    if 'PUBLISHER_NETWORK' in item['placements']:
                        ignored_line_item_count += 1
                        continue
                    if create_new_campaign:
                        item['start_time'] = campaign_data.get('start_time')
                        item['end_time'] = campaign_data.get('end_time')
                        item['paused'] = campaign_data.get('paused')
                    else:
                        campaign = \
                            TwitterCampaign.objects.get(pk=base36_to_int(campaign_id))
                        if campaign.start_time:
                            item['start_time'] = \
                                campaign.start_time.strftime('%Y-%m-%dT%H:%M:%S%z')
                        if campaign.end_time:
                            item['end_time'] = \
                                campaign.end_time.strftime('%Y-%m-%dT%H:%M:%S%z')
                        else:
                            item['end_time'] = None
                        item['paused'] = campaign.status != 'enabled'
                    name_to_ids[item['name']] = item['tw_line_item_id']
                    success_line_item_count += 1
                    line_items_data.append(item)
            if not line_items_data:
                return Response(
                        dict(error="All line items are TAP enabled so can't clone."),
                        status=status.HTTP_400_BAD_REQUEST)
            line_items_res = TwitterLineItem.batch_create(
                line_items_data,
                tw_account_id,
                oauth_token,
                oauth_token_secret)
            if not line_items_res['success']:
                return Response(
                    dict(error=line_items_res.get('error') or line_items_res.get('message')),
                    status=status.HTTP_400_BAD_REQUEST)

            line_items_data = line_items_res['data']
            targeting_data = []
            EXCLUDE_TARGETING_TYPES = (16,18)
            if not create_new_campaign:
                EXCLUDE_TARGETING_TYPES = (16, )

            for item in line_items_data:
                # set promotable tweets
                line_item_id = base36_to_int(item['id'])

                # if cloning line items to existing tw campaign, 
                # tweets are not provided. So original tweet ids from origin 
                # line item should be fetched
                if not create_new_campaign:
                    tw_tweet_ids = TwitterPromotedTweet.objects \
                            .filter(tw_line_item_id=name_to_ids[item['name']]) \
                            .values('tw_tweet_id')
                    tweet_ids = [str(r['tw_tweet_id']) for r in tw_tweet_ids]

                tweet_data = dict(
                        line_item_id=line_item_id,
                        tweet_ids=','.join(tweet_ids)
                    )

                tweet_res = TwitterPromotedTweet \
                    .set_promoted_tweet(tweet_data, tw_account_id)
                if not tweet_res['success']:
                    return Response(
                        dict(error=tweet_res.get('error') or \
                            tweet_res.get('message') or \
                            "Associating promotable tweets with" \
                                    " line item failed!"),
                        status=status.HTTP_400_BAD_REQUEST)

                # making targeting data
                targetings = TwitterTargeting.objects \
                    .filter(tw_line_item_id=name_to_ids[item['name']]) \
                    .exclude(tw_targeting_type__in=EXCLUDE_TARGETING_TYPES) \
                    .values()
                for t in targetings:
                    t['tw_line_item_id'] = line_item_id
                    del t['tw_criteria_id']

                    if not t['tw_targeting_type']:
                        ignored_targetings.append(t)
                        continue
                    # tailored audience
                    if t['tw_targeting_type'] == 18:
                        if not t['targeting_params'] or \
                            'EXCLUDED_' in t['targeting_params']:
                            t['operator_type'] = 'NE'
                        else:
                            t['operator_type'] = 'EQ'
                    targeting_data.append(t)

                # pick lowest platform version
                version_targeting = TwitterTargeting.objects.filter(
                        tw_line_item_id=name_to_ids[item['name']],
                        tw_targeting_type=16
                    ).order_by('tw_targeting_id').first()
                if version_targeting:
                    targeting_data.append(dict(
                            tw_line_item_id=line_item_id,
                            tw_targeting_type=16,
                            tw_targeting_id=version_targeting.tw_targeting_id
                        ))

                # tailored auidence part
                if create_new_campaign:
                    audience_fields = [
                        'excluded_tailored_audience',
                        'excluded_mobile_tailored_audience',
                        'included_tailored_audience',
                        'included_mobile_tailored_audience'
                    ]
                    for field in audience_fields:
                        if data.get(field):
                            for audience in data[field]:
                                audience['tw_line_item_id'] = line_item_id
                                targeting_data.append(audience)

            targeting_res = TwitterTargeting.set_targeting(
                targeting_data,
                tw_account_id,
                oauth_token,
                oauth_token_secret)

            if not targeting_res['success']:
                return Response(
                    dict(error=targeting_res.get('error') or targeting_res.get('message')),
                    status=status.HTTP_400_BAD_REQUEST)

            return Response(data=dict(
                    success=True,
                    success_line_item_count=success_line_item_count,
                    ignored_targetings=ignored_targetings,
                    ignored_line_item_count=ignored_line_item_count
                ))
        except Exception as e:
            traceback.print_exc()
            return Response(
                dict(error=str(e)),
                status=status.HTTP_400_BAD_REQUEST
            )
