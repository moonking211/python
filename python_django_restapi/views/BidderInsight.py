from collections import OrderedDict
from copy import deepcopy
import json
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import views
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
import urllib2

from mng.commons.crypto import encrypt
from restapi.models.Ad import Ad

from restapi.models.AdGroup   import AdGroup
from restapi.models.Zone import Zone
from restapi.models.base import PermissionDeniedException
from restapi.registry import REGISTRY


DPID_ANDROID = 'gaid:AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE'
DPID_IOS = 'ifa:AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE'
DPID_EXT = 'AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE'
UA_IOS_IPHONE = 'Mozilla/6.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) '\
                'AppleWebKit/536.26 (KHTML, like Gecko) Version/8.0 Mobile/10A5376e Safari/8536.25'
UA_IOS_IPAD = 'Mozilla/6.0 (iPad; CPU iPad OS 8_0 like Mac OS X) '\
              'AppleWebKit/536.26 (KHTML, like Gecko) Version/8.0 Mobile/10A5376e Safari/8536.25'
UA_ANDROID_MOBILE = 'Mozilla/5.0 (Linux; Android 5.0.2; VS415PP Build/KOT49I.VS415PP1) '\
                    'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 '\
                    'Mobile Safari/537.36'
UA_ANDROID_TABLET = 'Mozilla/5.0 (Linux; Android 5.0.2; SM-T230NU Build/KOT49H) '\
                    'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 '\
                    'Safari/537.36'

DEBUG_ADS_MAP = (('Trident Ads', 'debug_ads_TRIDENT'),                                              #L394,446
                 ('P1 Ads', 'debug_ads_OPTIMIZED'),
                 ('P2 Ads', 'debug_ads_LEARN'))


def bidder_api_call(payload, server_name, is_trident, is_raw, bidder_name=None):
    json_payload = json.dumps(payload)
    method = 'bid_debug_raw' if is_raw else 'bid_debug'
    if server_name[:7] == 'http://':
        url = "%s/2/%s?is_trident=%s" % (server_name, method, is_trident)
    else:
        url = "http://%s-bidder.%s.manage.com/2/%s?is_trident=%s" % (bidder_name, server_name, method, is_trident)

    result = None
    bidder_request = urllib2.Request(url, json_payload, {'Content-Type': 'application/json'})
    try:
        # pylint: disable=invalid-name
        f = urllib2.urlopen(bidder_request)
        # pylint: disable=unused-variable
        info = f.info()
        # pylint: disable=unused-variable
        status_code = f.getcode()
        bidder_response = f.read()
        f.close()
        result = json.loads(bidder_response, object_pairs_hook=OrderedDict)
    # pylint: disable=unused-variable,broad-except
    except Exception as error:
        pass

    return result


def get_grupped_ads(ads, custom_priority=None):                                                 #L192
    result = OrderedDict()
    priority = 1
    ads = sorted(ads or [], key=lambda ad: -ad['randomized_rpm'])                               #L201
    # pylint: disable=invalid-name
    for ad in ads:
        ad_group_id = ad['ad_group_id']
        rpm = round(float(ad['rpm']), 2)

        try:
            ad_status = Ad.objects.get(ad_id=ad['ad_id']).status
        except ObjectDoesNotExist:
            ad_status = None

        ad['status'] = ad_status

        entry = result.get(ad_group_id, None)
        if entry is None:
            ad_group = AdGroup.objects.filter(pk=int(ad_group_id))

            entry = {'priority': priority * 10,
                     'custom_priority': '' if custom_priority is None else custom_priority.get(ad_group_id, ''),
                     'ad_group_id': ad['ad_group_id'],
                     'campaign_id': ad['campaign_id'],
                     'event_type': ad['event_type'],
                     'event_rpm': ad['event_rpm'],
                     'frequency_cap': "%s/%s" % (ad['max_frequency'], ad['frequency_interval']),
                     'ads': [],
                     'max_rpm': rpm,
                     'min_rpm': rpm,
                     'line_index': len(result.keys())}

            if ad_group.exists():
                ad_group = ad_group.first()
                entry['advertiser_id'] = ad_group.campaign_id.advertiser_id_id
                entry['advertiser'] = ad_group.campaign_id.advertiser_id.advertiser
                entry['campaign'] = ad_group.campaign_id.campaign
                entry['ad_group'] = ad_group.ad_group

            result[ad_group_id] = entry
            priority += 1

        entry['ads'].append(ad)

        if rpm > entry['max_rpm']:
            entry['max_rpm'] = rpm

        if rpm < entry['min_rpm']:
            entry['min_rpm'] = rpm

    return result.values()


class BidderInsight(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def get(self, request):
        params = request.data if request.method == 'POST' else request.query_params
        bidder_name = params.get('bidder', None) or ''
        bidder_name = bidder_name.lower()
        server_name = params.get('bidder_machine', None) or 'insights-bidder'
        is_trident = params.get('is_trident', None)

        # check permissions
        user = REGISTRY.get('user', None)
        perm_field = 'publisher_bidder_insight' if bidder_name == 'appsponsor' else 'advertiser_bidder_insight'
        if not bool(user.get_permitted_model_fields(model='tools', action='read', fields=[perm_field])):
            raise PermissionDeniedException()

        raw_input_str = params.get('raw_request', None)
        is_raw = False
        if raw_input_str:
            payload = json.loads(raw_input_str)
            payload['manage_debug'] = 1
            is_raw = True
        elif bidder_name == 'appsponsor':                                                           #L48
            payload = self.get_payload_for_appsponsor(params)
            is_raw = True
        else:                                                                                       #L112
            payload = self.get_payload(params)

        bidder_data = bidder_api_call(payload, server_name, is_trident, is_raw, bidder_name)   #L153-158
        if bidder_data is None:
            bidder_data = dict()

        result = OrderedDict()
        # pylint: disable=unidiomatic-typecheck
        if type(bidder_data) == dict and 'Fail' in bidder_data:
            result['Fail'] = bidder_data['Fail']
            del bidder_data['Fail']
        # pylint: disable=unidiomatic-typecheck
        elif type(bidder_data) == dict and len(bidder_data.keys()) < 2:
            result['Fail'] = 'unknown reason'

        for key in ['chosen_ad', 'raw_request']:                                                    #L435,439,445,459
            if key in bidder_data:
                del bidder_data[key]

        # pylint: disable=invalid-name
        fn = self.prepare_result_appsponsor if bidder_name == 'appsponsor' else self.prepare_result #L299
        result.update(fn(request, bidder_data))

        return Response({'result': result})

    post = get

    # pylint: disable=no-self-use
    def get_params(self, params, names, defaults, strip=False):
        result = dict()
        for key in names:
            value = params.get(key, None)
            if value is not None:
                result[key] = value.strip() if strip else value
            elif key in defaults:
                result[key] = defaults[key]
        return result

    def get_payload(self, params):
        names = ['bidfloor', 'size', 'os', 'form_factor', 'osv', 'model', 'device_id',
                 'distribution', 'ad_type', 'placement_type', 'placement_id', 'country',
                 'region', 'dma', 'city', 'zip', 'cat', 'battr', 'bcat', 'bdomain']
        payload = self.get_params(params, names, {'cat': ''})
        if 'form_factor' in payload and payload['form_factor'] == '':                               #L116-118
            del payload['form_factor']
        device_id = payload.get('device_id', '')
        distribution = payload.get('distribution', '')
        payload['uh'] = "%s:%s" % (distribution[4:] if distribution[:3] == 'app' else 'web', device_id)
        return payload

    def get_payload_for_appsponsor(self, params):
        names = ['bidder', 'tz', 'ts', 'lang', 'bdn', 'bn', 'instl', 'form_factor', 'verify',
                 'voxel_version', 'sdkv', 'osv', 'nw', 'make', 'platform', 'zone_type', 'bidid',
                 'orient', 'bi', 'sd', 'nw', 'nl', 'country', 'ip']
        payload = self.get_params(params, names, {'sdkv': '3:1'}, strip=True)
        payload['manage_debug'] = 1                                                                 #L102
        zone_id = params.get('zone_id')
#        payload['zid'] = encrypt(zone_id)                                                           #L59
        payload['zid'] = zone_id # AMMYM-1701
        zone = Zone.objects.get(pk=int(zone_id))                                                    #L64
        # Size
        payload['width'], payload['height'] = tuple(params.get('size').split('x', 1))               #L75
        # OS and Model
        form_factor = payload.get('form_factor', '')
        # pylint: disable=invalid-name
        os = payload['os'] = zone.os                                                                #L78
        model = params.get('model', 'iPhone') if os == 'iOS' else 'Android'

        payload['dpid.ext'] = DPID_EXT
        payload['dpid'] = DPID_IOS if os == 'iOS' else DPID_ANDROID
        if os == 'iOS':
            payload['ua'] = UA_IOS_IPAD if model == 'iPad' else UA_IOS_IPHONE
        else:
            payload['ua'] = UA_ANDROID_TABLET if form_factor == 'android_tablet' else UA_ANDROID_MOBILE
        return payload

    # pylint: disable=no-self-use
    def prepare_result_appsponsor(self, request, bidder_data):
        data = deepcopy(bidder_data)
        params = request.data if request.method == 'POST' else request.query_params
        model = params.get('model')
        country = params.get('country')
        action = params.get('action', '')
        is_trident = params.get('is_trident', True)
        zone_id = params.get('zone_id')
        zone = Zone.objects.get(pk=int(zone_id))

        if action in ['update_priority', 'update_json']:                                            #L304
            existing_custom_priority = OrderedDict()
            if zone.custom_priority:
                existing_custom_priority = json.loads(zone.custom_priority, object_pairs_hook=OrderedDict)
            new_custom_priority = None

            if action == 'update_priority':                                                         #L320
                # Load new priority
                custom_priority = OrderedDict()
                for key, value in params.items():
                    if key.startwith('priority_'):
                        ad_group_id = key.split('_')[1]
                        custom_priority[ad_group_id] = value

                # Re-order new priority
                new_priority = 1
                for ad_group_id in sorted(custom_priority.keys()):
                    new_custom_priority[ad_group_id] = new_priority * 10
                    new_priority += 1
            else:                                                                                   #L336
                # Update JSON directly
                custom_priority_json = params.get('custom_priority_json')
                new_custom_priority = custom_priority_json if custom_priority_json else {}

            if new_custom_priority is not None:                                                     #L351
                # Update existing custom_priority
                if not new_custom_priority:
                    del existing_custom_priority[country][model]
                    if not existing_custom_priority[country]:
                        del existing_custom_priority[country]
                else:
                    if country not in existing_custom_priority:
                        existing_custom_priority[country] = {}
                    existing_custom_priority[country][model] = new_custom_priority

                zone.custom_priority = json.dumps(existing_custom_priority) if existing_custom_priority else ''
                zone.save()

        custom_priority = None
        if is_trident:
            custom_priority = OrderedDict()
            if zone.custom_priority:
                json_custom_priority = json.loads(zone.custom_priority, object_pairs_hook=OrderedDict)
                if country in json_custom_priority and model in json_custom_priority[country]:
                    custom_priority = json_custom_priority[country][model]

        ads = OrderedDict()
        result = {'ads': ads,
                  'app': zone.app,
                  'zone': zone.zone,
                  'os': zone.os,
                  'zone_ad_type': zone.ad_type_title,
                  'custom_priority': custom_priority}

        for key, bidder_key in DEBUG_ADS_MAP:
            if bidder_key in data:
                ads[key] = get_grupped_ads(data.pop(bidder_key))

        result['bidder_data'] = [{k: v} for k, v in data.items()]
        return result

    # pylint: disable=no-self-use,unused-argument
    def prepare_result(self, request, bidder_data):
        ads = OrderedDict()
        result = {'ads': ads}
        data = deepcopy(bidder_data)

        for key, bidder_key in DEBUG_ADS_MAP:
            if bidder_key in data:
                ads[key] = get_grupped_ads(data.pop(bidder_key))

        result['bidder_data'] = [{k: v} for k, v in data.items()]
        return result


