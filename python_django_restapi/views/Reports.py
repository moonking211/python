import StringIO
from copy import copy
import csv
import json
from django.conf import settings
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from restapi.models.Ad import Ad
from restapi.models.AdGroup import AdGroup
from restapi.models.Advertiser import Advertiser
from restapi.models.Agency import Agency
from restapi.models.Campaign import Campaign
from restapi.models.TradingDesk import TradingDesk
from restapi.registry import REGISTRY
import requests


class Reports(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )
    
    trading_desk_key = None
    trading_desk_ids = None
    path = None
    items_cache = None
    select = None

    models = {'agency': Agency,
              'advertiser': Advertiser,
              'campaign': Campaign,
              'ad_group': AdGroup,
              'ad': Ad}

    def dispatch(self, request, path):
        self.items_cache = {}
        self.path = path

        user = REGISTRY.get('user', None)
        self.user = user

        select = request.GET.get('$select', None)
        if select is not None:
            self.select = select.split(',')

        trading_desk = user.profile.trading_desk.first()
        if trading_desk is None:
            return HttpResponse('{"HTTP-STATUS": 403}', status=200)
        self.trading_desk_key = trading_desk.trading_desk_key

        trading_desk_ids = [str(t.pk) for t in TradingDesk.objects.all()]
        filter_by_trading_desk_id = request.GET.get('filter_by_trading_desk_id', '')
        if filter_by_trading_desk_id != '':
            trading_desk_ids = [i for i in trading_desk_ids if i in filter_by_trading_desk_id.split(",")]
        if not trading_desk_ids:
            return HttpResponse('{"HTTP-STATUS": 403}', status=200)
        self.trading_desk_ids = trading_desk_ids

        return super(Reports, self).dispatch(request)

    def get_url(self):
        url = str(settings.STATS_API_DOMAIN) \
              + str(settings.ADVERTISER_STATS_API_PATH) \
              + str(self.path) \
              + '?' + self.get_query()
        return url

    def get_query(self):
        get_params = copy(self.request.GET)

        get_params['format'] = 'csv'

        get_params['filter_by_trading_desk_id'] = ",".join(self.trading_desk_ids)

        break_by = get_params.get('break_by', "")
        break_by = break_by.split(",") if break_by else []
        for param in get_params.keys():
            if param[:7] == 'filter_' and param[-5:] == '_like':
                filter_name = param[7:-5]
                if filter_name not in break_by:
                    break_by.append(filter_name)
        get_params['break_by'] = ",".join(break_by)

        params = ['%s=%s' % (k, get_params[k]) for k in get_params.keys()]
        return '&'.join(params)

    def get_item(self, headers, data, name):
        if name == 'ad':
            cached = {}
        else:
            if name not in self.items_cache:
                self.items_cache[name] = {}
            cached = self.items_cache[name]

        pk = None
        try:
            index = headers.index('%s_id' % name)
            pk = int(data[index])
        except ValueError:
            pass

        item = None
        if pk is not None:
            if pk not in cached:
                cached[pk] = None
                qs = self.models[name].objects.filter(pk=pk)
                if qs.exists():
                    cached[pk] = qs.first()
            item = cached[pk]
        return item

    def update_headers(self, headers) :
        extra_headers = {'ad_id':        ['trading_desk_id','agency_id','advertiser_id','campaign_id','ad_group_id','ad_type','i_url','html','size','ad_preview'],
                         'ad_group_id':  ['trading_desk_id','agency_id','advertiser_id','campaign_id'],
                         'campaign_id':  ['trading_desk_id','agency_id','advertiser_id'],
                         'advertiser_id':['trading_desk_id','agency_id'],
                         'agency_id':    ['trading_desk_id'],
                         'revenueA':     ['revenueA_per_install'],
                         'revenueB':     ['revenueB_per_install'],
                         'revenueC':     ['revenueC_per_install'],
                         'revenueD':     ['revenueD_per_install'],
                         'revenueE':     ['revenueE_per_install']}

        for f in ['margin', 'win_rate','cpm','rpm','cpi','rpi','ctr','ir']:
            if f not in headers:
                headers.append(f)
        for header in extra_headers:
            if header in headers:
                for extra in extra_headers[header]:
                    if extra not in headers:
                        headers.append(extra)

    def update_data(self, headers, data):
        for i in range(len(headers)-len(data)):
            data.append('')

        def _update(name, value):
            data[headers.index(name)] = value

        def _get(name, data_type=None):
            value = data[headers.index(name)]
            if data_type is not None:
                value = data_type(value)
            return value

        for name in ['agency', 'advertiser', 'campaign', 'ad_group', 'ad']:
            item = self.get_item(headers, data, name)

            if item is None:
                continue

            _update(name, str(item))

            if name == 'ad':
                _update('i_url', item.i_url)
                _update('html', item.html)
                _update('ad_preview', item.i_url or item.html)
                _update('size', item.size)
                _update('ad_group_id', item.ad_group_id_id)
                _update('ad_type', item.ad_type)
                _update('campaign_id', item.campaign_id)
                _update('advertiser_id', item.advertiser_id)
                _update('agency_id', item.agency_id)
                _update('trading_desk_id', item.trading_desk_id)

            elif name == 'ad_group':
                _update('campaign_id', item.campaign_id_id)
                _update('advertiser_id', item.advertiser_id)
                _update('agency_id', item.agency_id)
                _update('trading_desk_id', item.trading_desk_id)

            elif name == 'campaign':
                _update('advertiser_id', item.advertiser_id_id)
                _update('agency_id', item.agency_id)
                _update('trading_desk_id', item.trading_desk_id)

            elif name == 'advertiser':
                _update('agency_id', item.agency_id_id)
                _update('trading_desk_id', item.trading_desk_id)

            elif name == 'agency':
                _update('trading_desk_id', item.trading_desk_id_id)

        try:
            _update('margin', round(_get('profit', float) / _get('revenue', float) * 100, 2))
        except:
            pass

        impression = 0
        ibidresponse = 0
        install = 0
        try:
            impression = _get('impression', float)
            ibidresponse = _get('i-bid_response', float)
            install = _get('install', float)
        except:
            pass

        # win_rate
        win_rate = round(impression / ibidresponse * 100., 2) if ibidresponse else 0
        _update('win_rate', win_rate)

        # cpm, rpm
        try:
            cpm = round(_get('cost', float) / impression * 1000, 2)
            rpm = round(_get('revenue', float) / impression * 1000, 2)
        except:
            cpm = 0
            rpm = 0
        _update('cpm', cpm)
        _update('rpm', rpm)

        # cpi, rpi
        try:
            cpi = round(_get('cost', float) / install, 2)
            rpi = round(_get('revenue', float) / install, 2)
        except:
            cpi = 0
            rpi = 0
        _update('cpi', cpi)
        _update('rpi', rpi)

        # ctr
        try:
            ctr = round(_get('click', float) / impression * 100, 2)
        except:
            ctr = 0
        _update('ctr', ctr)

        # ir
        try:
            ir = round(install / _get('click', float) * 100, 2)
        except:
            ir = 0
        _update('ir', ir)

        for name in ['revenueA', 'revenueB', 'revenueC', 'revenueD', 'revenueE']:
            if name in headers:
                try:
                    value = _get(name, float) / install * 100
                except:
                    value = 0
                _update('%s_per_install' % name, value)

    def select_data(self, headers, data):
        if self.select:
            indexes = [headers.index(f) for f in self.select if f in headers]
            data = [data[i] for i in indexes]
        return data

    def get(self, request):
        headers = {'Authorization': 'token token="%s"' % self.trading_desk_key}
        api_response = requests.get(self.get_url(), headers=headers, verify=False, stream=True)

        status_code = int(api_response.status_code)
        content_type = api_response.headers.get('content-type', 'text/csv')

        if status_code != 200:
            data = json.dumps({'info': api_response.text})
            return HttpResponse(data, status=status_code, content_type=content_type)

        if content_type != 'text/csv':
            return HttpResponse(api_response.text, status=status_code, content_type=content_type)

        this = self
        def stream_response_generator():
            data = []
            headers = []
            headers_ready = False
            for line in api_response.iter_lines():
                data = csv.reader([line]).next()
                if not headers_ready:
                    headers = data
                    this.update_headers(headers)
                    headers_ready = True
                else:
                    this.update_data(headers, data)

                output = StringIO.StringIO()
                writer = csv.writer(output)
                row = this.select_data(headers, data)
                writer.writerow(row)
                yield output.getvalue()

        response = StreamingHttpResponse(stream_response_generator(), status=status_code, content_type=content_type)
        response['Content-Disposition'] = 'inline; filename="report.csv'

        return response
