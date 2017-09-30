import StringIO
from copy import copy
import csv
import json
from django.conf import settings
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from restapi.models.Campaign import Campaign
from restapi.models.TradingDesk import TradingDesk
from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.models.twitter.TwitterCampaign import TwitterCampaign
from restapi.models.twitter.TwitterTweet import TwitterTweet
from restapi.models.Campaign import Campaign
from restapi.models.twitter.TwitterAppCard import TwitterAppCard
from restapi.registry import REGISTRY
import requests


class TWReports(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )
    
    trading_desk_key = None
    trading_desk_ids = None
    path = None
    items_cache = None
    select = None
    os_names = ['Android', 'iOS']

    models = {
        'tw_promoted_tweet_id': TwitterPromotedTweet,
        'tw_line_item_id':  TwitterLineItem,
        'tw_campaign_id':  TwitterCampaign,
        'campaign_id': Campaign
    }

    extra_headers = {'tw_promoted_tweet_id': ['advertiser_id', 'campaign_id', 'tw_campaign_id', 'tw_line_item_id'],
                         'tw_line_item_id':  ['advertiser_id', 'campaign_id', 'tw_campaign_id'],
                         'tw_campaign_id':  ['advertiser_id', 'campaign_id'],
                         'campaign_id': ['advertiser_id']}

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

        return super(TWReports, self).dispatch(request)

    def get_url(self):
        url = str(settings.TWITTER_STATS_API_DOMAIN) \
              + str(settings.ADVERTISER_STATS_API_PATH) \
              + str(self.path) \
              + '?' + self.get_query()

        return url

    def get_query(self):
        get_params = copy(self.request.GET)

        get_params['format'] = 'csv'

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

    def get_item(self, headers, data, id_name):
        if id_name not in self.items_cache:
            self.items_cache[id_name] = {}
        cached = self.items_cache[id_name]

        pk = None
        try:
            index = headers.index(id_name)
            pk = int(data[index])
        except ValueError:
            pass

        item = None
        if pk is not None:
            if pk not in cached:
                cached[pk] = None
                qs = self.models[id_name].objects_raw.filter(pk=pk)
                if qs.exists():
                    cached[pk] = qs.first()
            item = cached[pk]
        return item

    def update_headers(self, headers):


        for f in ['conversion', 'engagement_rate', 'cpac', 'manage_cost', 'app_click_rate', 'cpc', 'conversion_rate', 'cpi',
                  'cpm', 'app_click', 'service_fee', 'service_fee_rate']:
            if f not in headers:
                headers.append(f)
        if 'tw_promoted_tweet_id' in headers:
            headers.append('tw_promoted_tweet_preview')
            headers.append('tw_video_player_url')

        for header in self.extra_headers:
            if header in headers:
                for extra in self.extra_headers[header]:
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

        for name in ['tw_campaign', 'tw_line_item']:
            if name in headers:
                _update(name, '%s(%s)' % (_get(name), _get(name+'_id')))

        item = None
        for id_name in self.extra_headers:
            if id_name in headers:
                item = self.get_item(headers, data, id_name)
                if item:
                    for f in self.extra_headers[id_name]:
                        _update(f, getattr(item, '_' + f))
                break

        if 'tw_promoted_tweet_id' in headers and item:
            try:
                tweet = TwitterTweet.objects.get(pk=item.tw_tweet_id)
                _update('tw_promoted_tweet_preview', tweet.text.encode('utf8'))
                app_card = TwitterAppCard.objects.filter(tw_app_card_id=item.tw_app_card_id).first()
                video_player_url = ''
                if app_card:
                    if app_card.video_poster_url and app_card.video_url:
                        video_player_url = "https://amp.twimg.com/amplify-web-player/prod/source.html?json_rpc=1&square_corners=1&image_src=%s&vmap_url=%s" % (app_card.video_poster_url, app_card.video_url)
                _update('tw_video_player_url', video_player_url)
            except:
                _update('tw_promoted_tweet_preview', '')
                _update('tw_video_player_url', '')
        if 'os_campaign' in headers:
            _update('os_campaign', self.os_names[int(_get('os_campaign'))])

        try:
            _update('margin', round(_get('profit', float) / _get('revenue', float) * 100, 2))
        except:
            pass

        install = _get('install', int)
        impression = _get('impression', float)
        app_open = _get('app_open', int)
        # conversion
        try:
            conversion = install + app_open
        except:
            conversion = 0

        _update('conversion', conversion)

        # engagement_rate
        try:
            _update('engagement_rate', round(_get('engagement', float) * 100 / impression, 2))
        except:
            pass

        # cpac
        try:
            _update('cpac', round(_get('mcost', float) / _get('click', float), 2))
        except:
            pass

        # app_click_rate
        try:
            app_click_rate = round(_get('click', float) / impression * 100, 2)
        except:
            app_click_rate = 0
        _update('app_click_rate', app_click_rate)

        # conversion_rate
        try:
            conversion_rate = round(install / _get('click', float) * 100, 2)
        except:
            conversion_rate = 0
        _update('conversion_rate', conversion_rate)

        # cpi
        try:
            cpi = round(_get('mcost', float) / install, 2)
        except:
            cpi = 0
        _update('cpi', cpi)

        # cpm
        try:
            cpm = round(_get('mcost', float) / impression * 1000, 2)
        except:
            cpm = 0
        _update('cpm', cpm)

        # service fee
        service_fee = round(_get('revenue', float) - _get('cost', float), 2)
        _update('service_fee', service_fee)

        # service fee rate
        try:
            service_fee_rate = round(service_fee / _get('mcost', float) * 100, 2)
        except:
            service_fee_rate = 0
        _update('service_fee_rate', service_fee_rate)

        _update('manage_cost', round(_get('cost', float), 2))
        _update('app_click', _get('click'))

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
