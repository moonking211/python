# encoding: utf-8

from __future__ import unicode_literals

import collections
from copy import copy
import csv
import datetime
import json

import six
import requests

from django.conf import settings
from django.core.cache import cache as redis_cache
from django import http
from django.http import HttpResponse

from rest_framework import permissions
from rest_framework.decorators import permission_classes

from restapi import core
from restapi.models import TradingDesk
from restapi.models import Agency
from restapi.models import Advertiser
from restapi.models import Campaign
from restapi.models import AdGroup
from restapi.models import Ad
from restapi.models.base import PermissionDeniedException
from restapi.registry import REGISTRY

_FIELDS_BY_MODEL_NAME = {
    'agency': ('agency_id', 'trading_desk_id'),
    'advertiser': ('advertiser_id', 'agency_id', 'agency_id__trading_desk_id'),
    'campaign': (
        'campaign_id',
        'advertiser_id',
        'advertiser_id__agency_id__trading_desk_id',
        'advertiser_id__agency_id'
    ),
    'ad_group': (
        'campaign_id',
        'campaign_id__advertiser_id',
        'campaign_id__advertiser_id__agency_id',
        'campaign_id__advertiser_id__agency_id__trading_desk_id'
    ),
    'ad': (
        'i_url',
        'html',
        'size',
        'ad_type',
        'ad_group_id',
        'ad_group_id__campaign_id',
        'ad_group_id__campaign_id__advertiser_id',
        'ad_group_id__campaign_id__advertiser_id__agency_id',
        'ad_group_id__campaign_id__advertiser_id__agency_id__trading_desk_id'
    )
}

_MODEL_BY_NAME = {
    'agency': Agency.Agency,
    'advertiser': Advertiser.Advertiser,
    'campaign': Campaign.Campaign,
    'ad_group': AdGroup.AdGroup,
    'ad': Ad.Ad
}


@permission_classes((permissions.IsAuthenticated,))
def audience_proxy(request, path):
    """
    Proxy to use cross domain Ajax GET and POST requests
    request: Django request object
    """
    if request.method not in {'GET', 'POST'}:
        return http.HttpResponseNotAllowed(('GET', 'POST'))

    url = '%s%s' % (settings.AUDIENCE_BUILDER_API, path)

    if request.method == 'POST':
        data = request.body
        r = requests.post
    else:
        request = request.GET
        r = requests.get
        data = json.dumps(request)

    response = r(url, data=data, headers={'content-type': 'application/json'}, verify=False)

    return http.HttpResponse(response.text, status=int(response.status_code), content_type="application/json")


@permission_classes((permissions.IsAuthenticated,))
def advertiser_stats_proxy(request, token, path):
    """
    Proxy to use cross domain Ajax GET requests
    request: Django request object
    """
    user = REGISTRY.get('user', None)
    trading_desk = user.profile.trading_desk.first()
    if trading_desk:
        token = trading_desk.trading_desk_key
    else:
        advertiser = user.profile.advertisers.first()
        if advertiser is None:
            raise PermissionDeniedException()
        token = advertiser.advertiser_key

    if request.GET.get('source_type') == '2':
        url = ''.join([settings.TWITTER_STATS_API_DOMAIN, settings.ADVERTISER_STATS_API_PATH, path])
    else:
        url = ''.join([settings.STATS_API_DOMAIN, settings.ADVERTISER_STATS_API_PATH, path])

    trading_desk_ids = map(str, TradingDesk.TradingDesk.objects.values_list('trading_desk_id', flat=True))
    get_params = copy(request.GET)

    should_cache = get_params.get('should_cache')
    if should_cache:
        del get_params['should_cache']
        # get end date (frontend user timezone) user timezone yesterday could be today in stats API timezone
        end_date = get_params['date_to']

        # get today str (Monarch, Stats API timezone)
        _today = datetime.date.today().strftime('%Y-%m-%d')
        should_cache = _today > end_date and datetime.datetime.now().hour > 7

    filter_by_trading_desk_id = get_params.get('filter_by_trading_desk_id', '')
    if filter_by_trading_desk_id != '':
        filter_ids = get_params['filter_by_trading_desk_id'].split(',')
        trading_desk_ids = map(str, [i for i in trading_desk_ids if i in filter_ids])

    ad_id = get_params.get('filter_by_ad_id')
    ad_group_id = get_params.get('filter_by_ad_group_id')
    if ad_id and not ad_group_id:
        try:
            ad_group_id = Ad.Ad.objects.get(pk=ad_id).ad_group_id.pk
            get_params['filter_by_ad_group_id'] = ad_group_id
        except:
            pass

    campaign_id = get_params.get('filter_by_campaign_id')
    if ad_group_id and not campaign_id:
        try:
            campaign_id = AdGroup.AdGroup.objects.get(pk=ad_group_id).campaign_id.pk
            get_params['filter_by_campaign_id'] = campaign_id
        except:
            pass

    advertiser_id = get_params.get('filter_by_advertiser_id')
    if campaign_id and not advertiser_id:
        try:
            advertiser_id = Campaign.Campaign.objects.get(pk=campaign_id).advertiser_id.pk
            get_params['filter_by_advertiser_id'] = advertiser_id
        except:
            pass

    if not trading_desk_ids:
        return http.JsonResponse({'HTTP-STATUS': 403, 'success': False}, safe=True, status=403)

    get_params['filter_by_trading_desk_id'] = ','.join(trading_desk_ids)

    break_by = get_params.get('break_by', '')
    break_by = break_by.split(',') if break_by else []
    for param in get_params.keys():
        if param[:7] == 'filter_' and param[-5:] == '_like':
            filter_name = param[7:-5]
            if filter_name not in break_by:
                break_by.append(filter_name)
    get_params['break_by'] = ','.join(break_by)

    params = ['%s=%s' % (k, get_params[k]) for k in get_params.keys()]
    query = '&'.join(params)
    data = redis_cache.get(query, False)
    if data:
        content_type = 'application/json'
        status_code = 200
    else:
        url = url + '?' + query
        headers = {'Authorization': 'token token="%s"' % token}
        response = requests.get(url, headers=headers, verify=False)

        status_code = int(response.status_code)
        data = response.text

        content_type = response.headers.get('content-type', 'application/json')

        if content_type == 'text/json':
            content_type = 'application/json'

        if content_type == 'text/csv':
            csv_reader = csv.DictReader(six.StringIO(response.text))
            permitted_fields = set(request.user.get_permitted_model_fields('metrics', 'read', csv_reader.fieldnames))
            remap_fields = {}
            if request.user.profile.advertisers.exists():
                # IMPORTANT: If user has advertiser than it's advertiser user and we should display cost as a spend.
                remap_fields['cost'] = 'spend'
            out = six.StringIO()
            field_names = [f for f in csv_reader.fieldnames if f in permitted_fields]
            csv_writer = csv.DictWriter(out, [remap_fields.get(f, f) for f in field_names])
            csv_writer.writeheader()
            for row in csv_reader:
                csv_writer.writerow({remap_fields.get(k, k): v for k, v in six.iteritems(row) if k in field_names})
            data = out.getvalue()
        elif content_type == 'application/json':
            json_data = json.loads(data)
            entity_by_id_by_model_name = collections.defaultdict(dict)
            for name in {'advertiser', 'campaign', 'ad_group', 'ad'}:
                key = '{}_id'.format(name)
                ids = list(set(core.safe_to_int(item_id) for item_id in (i.get(key) for i in json_data) if item_id))
                if ids:
                    model = _MODEL_BY_NAME[name]
                    fields = _FIELDS_BY_MODEL_NAME[name]
                    if key not in fields:
                        fields += (key,)
                    for item in model.objects.filter(**{'{}__in'.format(key): ids}).values(*fields):
                        entity_by_id_by_model_name[name][item[key]] = {k.split('__')[-1]: v
                                                                       for k, v in six.iteritems(item) if k != key}
                    for i in json_data:
                        item_id = core.safe_to_int(i[key])
                        if item_id in entity_by_id_by_model_name[name]:
                            i.update(entity_by_id_by_model_name[name][item_id])
            data = json.dumps(json_data)

        if status_code != 200:
            data = json.dumps({'info': data})
        elif should_cache and content_type != 'text/csv':
            # cache only if status_code is 200
            # expire after 2 days
            redis_cache.set(query, data, 60 * 60 * 24 * 2)

    response = HttpResponse(data, status=status_code, content_type=content_type)
    if content_type == 'text/csv':
        response['Content-Disposition'] = 'inline; filename="report.csv"'

    return response
