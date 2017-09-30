from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.serializers.twitter.TwitterLineItemSerializer import TwitterLineItemSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate
from rest_framework.response import Response
from django.db.models import Q
from copy import copy
from rest_framework import status
from restapi.models.twitter.TwitterTargetingModels import *
from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
import itertools
from compiler.ast import flatten
from django.utils.http import int_to_base36, base36_to_int


class TwitterLineItemList(BaseListCreate):
    serializer_class = TwitterLineItemSerializer
    contains_filter_include_pk = True
    query_filter_fields = ('tw_line_item_id', 'name')
    order_fields = ('name', '-name', 'last_updated', '-last_updated', 'created_at', '-created_at', )

    def get_queryset(self):
        filters = {}
        advertiser_id = self.request.query_params.get('advertiser_id')
        campaign_id = self.request.query_params.get('campaign_id')
        tw_campaign_id = self.request.query_params.get('tw_campaign_id')
        tw_line_item_ids = self.request.query_params.get('tw_line_item_ids')
        status = self.request.query_params.get('status')
        country = self.request.query_params.get('country')
        keyword = self.request.query_params.get('keyword')
        handle = self.request.query_params.get('handle')


        query_set = TwitterLineItem.objects
        if advertiser_id:
            filters['tw_campaign_id__campaign_id__advertiser_id'] = advertiser_id

        if campaign_id:
            filters['tw_campaign_id__campaign_id'] = campaign_id

        if tw_campaign_id:
            filters['tw_campaign_id__in'] = tw_campaign_id.split(',')

        if tw_line_item_ids:
            filters['tw_line_item_id__in'] = tw_line_item_ids.split(',')

        if status:
            filters['status__in'] = status.split(',')

        query_set = query_set.filter(**filters)

        if country:
            country = [c.strip() for c in country.split(',')]
            query_set = query_set.filter(Q(tw_targeting__name__in=country, tw_targeting__tw_targeting_type=2))
        if handle:
            handle = [c.strip() for c in handle.split(',')]
            query_set = query_set.filter(Q(tw_targeting__name__in=handle, tw_targeting__tw_targeting_type=9))
        if keyword:
            keyword = [c.strip() for c in keyword.split(',')]
            query_set = query_set.filter(Q(tw_targeting__name__in=keyword, tw_targeting__tw_targeting_type=10))

        return query_set.distinct()

    def create(self, request, *args, **kwargs):
        data = copy(request.data)
        data['paused'] = data['status'] != 'enabled'
        targetings = data['targeting_obj']
        #calc bulk values
        products = []

        def append_product_vals(vals):
            temp = []
            for v in vals:
                if v['val']:
                    temp.append(v['val'])
            if temp:
                products.append(temp)

        append_product_vals(targetings.get('app_categories', []))
        if data.get('target_each_country') and targetings.get('location'):
            products.append(targetings['location'])
        append_product_vals(targetings.get('interests', []))

        if not data.get('separate_keyword_follower'):
            append_product_vals(targetings.get('handles', []))
            append_product_vals(targetings.get('keywords', []))
            products = list(itertools.product(*products))
        else:
            temp = copy(products)
            append_product_vals(targetings.get('handles', []))
            _products = list(itertools.product(*products))
            products = temp
            append_product_vals(targetings.get('keywords', []))
            products = _products + list(itertools.product(*products))


        targeting_data = []
        line_items_data = []
        base_line_item_data = {
            'paused': data['paused'],
            'name': data.get('name'),
            'start_time': data.get('start_time'),
            'end_time': data.get('end_time'),
            'campaign_id': int_to_base36(data.get('campaign_id')),
            'bid_amount_local_micro': data.get('bid_amount_local_micro')
        }
        _index = 0

        safe_targeting_fields = (
            'os_version',
            'device',
            'carriers',
            'included_tailored_audience',
            'included_mobile_tailored_audience',
            'excluded_mobile_tailored_audience',
            'excluded_mobile_tailored_audience',
            'events',
        )

        for p in products:
            temp = []
            temp.append(p)

            for f in safe_targeting_fields:
                if targetings.get(f):
                    temp.append(targetings[f])

            if not data.get('target_each_country') and targetings['location']:
                temp.append(targetings['location'])

            temp = flatten(temp)
            # check wi-fi targeting
            if data.get('wifi_only'):
                temp.append({
                    'targeting_value': 1,
                    'tw_targeting_id': '',
                    'tw_targeting_type': 5
                })
            # check platform targeting
            flag = True # platform targeting should be added
            for l in temp:
                if l['tw_targeting_type'] in [4, 16]: # if device or min_verison is there
                    flag = False
                    break
            if flag:
                temp.append({
                    'targeting_value': '0' if targetings['os'] == 'iOS' else '1',
                    'tw_targeting_type': 3,
                    'tw_targeting_id': ''
                })
            # get location targetings
            location_targetings = []
            for l in temp:
                if l['tw_targeting_type'] == 2:
                    location_targetings.append(l)

            if len(location_targetings) == 1:
                # set tv targeting
                location_id = location_targetings[0]['tw_targeting_id']
                tv = targetings['tv'].get(location_id)
                if tv:
                    temp.append(tv['shows'])
                    temp.append(tv['channels'])
                    temp.append(tv['genres'])
                # set behavior targeting
                behavior = targetings['behaviors'].get(location_id)
                if behavior:
                    temp.append(behavior['vals'])



            # set line item data
            line_item_data = copy(base_line_item_data)
            line_item_name = '%s_' % line_item_data['name']
            if location_targetings:
                line_item_name += TwitterLocation.objects_raw.get(tw_targeting_id=location_targetings[0]['tw_targeting_id']).country_code3
            _index += 1
            line_item_name = '%s_%s_%s' % (line_item_name, targetings['os'], _index)
            line_item_data['name'] = line_item_name
            line_items_data.append(line_item_data)
            temp = flatten(temp)
            for t in temp:
                tt = copy(t)
                tt['name'] = line_item_name
                targeting_data.append(tt)

        # create batch line items
        account_id = data.get('tw_account_id')
        cpi_target_goal = data.get('cpi_target_goal')
        line_items_res = TwitterLineItem.batch_create(line_items_data, account_id)
        if line_items_res['success']:
            for line_item_res in line_items_res['data']:
                tw_line_item_id = base36_to_int(line_item_res['id'])
                line_item_name = line_item_res['name']
                for t in targeting_data:
                    if t['name'] == line_item_name:
                        t['tw_line_item_id'] = tw_line_item_id
                tweets_data = {
                    'line_item_id': tw_line_item_id,
                    'tweet_ids': ','.join(data.get('tweet_ids', []))
                }
                promoted_res = TwitterPromotedTweet.set_promoted_tweet(tweets_data, account_id)
                if not promoted_res['success']:
                    return Response(dict(message="Associating promotable tweets with line item \"%s\" was failed..." % line_item_name), status=status.HTTP_400_BAD_REQUEST)


                line_item = TwitterLineItem.objects_raw.get(pk=tw_line_item_id)
                revmap, created = TwitterRevmap.objects_raw.get_or_create(campaign_id=line_item.tw_campaign_id.campaign_id,
                                                    tw_campaign_id=line_item.tw_campaign_id.pk, tw_line_item_id=line_item.pk)
                revmap.opt_type = 'install'
                revmap.opt_value = cpi_target_goal
                revmap.save()

            # set batch targetings
            targetings_res = TwitterTargeting.set_targeting(targeting_data, account_id)
            if not targetings_res['success']:
                return Response(dict(message=targetings_res['error']['messages']), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(dict(message=line_items_res.get('error') or line_items_res.get('message')), status=status.HTTP_400_BAD_REQUEST)

        return Response(dict(status='ok'))
