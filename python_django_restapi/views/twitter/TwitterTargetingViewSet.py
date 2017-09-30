from restapi.models.twitter.TwitterTargetingModels import *
from restapi.serializers.twitter.TwitterTargetingSerializer import *
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework import filters
from restapi.views.base_view.BaseDetail import BaseDetail
from rest_framework.response import Response
import django_filters
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.views.twitter.helper import human_format
from django.conf import settings

class TwitterTargetingListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterTargetingSerializer
    queryset = TwitterTargeting.objects.all()
    search_fields = ('name', )
    filter_backends = (filters.SearchFilter, )

    @property
    def queryset(self):
        return TwitterTargeting.objects.all()

class TwitterTargetingDetail(BaseDetail):
    serializer_class = TwitterTargetingSerializer

    @property
    def queryset(self):
        return TwitterTargeting.objects.all()

class TwitterLocationListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterLocationSerializer
    queryset = TwitterLocation.objects.filter(location_type='Countries').all()
    search_fields = ('location_name', )
    filter_backends = (filters.SearchFilter, )

class TwitterAppCategoryListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterAppCategorySerializer
    queryset = TwitterAppCategory.objects.all()
    search_fields = ('app_category', )
    filter_backends = (filters.SearchFilter, )

    def get_queryset(self):
        queryset = TwitterAppCategory.objects.all().exclude(app_category='Games')
        if self.request.query_params.get('platform'):
            queryset = queryset.filter(platform=self.request.query_params['platform'])
        return queryset

class TwitterUserInterestListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterUserInterestSerializer
    queryset = TwitterUserInterest.objects.all()

    def get_queryset(self):
        queryset = TwitterUserInterest.objects.all()
        if self.request.query_params.get('not_parent'):
            queryset = queryset.exclude(subcategory='')
        return queryset

class TwitterCarrierListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterCarrierSerializer
    queryset = TwitterCarrier.objects.all()
    search_fields = ('carrier_name', )
    filter_backends = (filters.SearchFilter, )

class TwitterOsVersionListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterOsVersionSerializer
    queryset = TwitterOsVersion.objects.all()
    filter_backends = (filters.SearchFilter, )

    def get_queryset(self):
        queryset = TwitterOsVersion.objects.all()
        if self.request.query_params.get('platform'):
            queryset = queryset.filter(platform=self.request.query_params['platform'])
        return queryset


class TwitterDeviceListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterDeviceSerializer
    queryset = TwitterDevice.objects.all()
    search_fields = ('device', )
    filter_backends = (filters.SearchFilter, )
    
    def get_queryset(self):
        queryset = TwitterDevice.objects.all()
        if self.request.query_params.get('platform'):
            queryset = queryset.filter(platform=self.request.query_params['platform'])
        return queryset

class TwitterTVMarketListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterTVMarketSerializer
    queryset = TwitterTVMarket.objects.all()


class TwitterTVGenreListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterTVGenreSerializer
    queryset = TwitterTVGenre.objects.all()


class TwitterTVChannelListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterTVChannelSerializer

    def get_queryset(self):
        queryset = TwitterTVChannel.objects
        tw_tv_market_id = self.request.query_params.get('tw_tv_market_id')
        if tw_tv_market_id:
            tv_market = TwitterTVMarket.objects_raw.get(pk=tw_tv_market_id)
            queryset = tv_market.tv_channels
        query = self.request.query_params.get('query')
        if query:
            queryset = queryset.filter(name__icontains=query)

        return queryset.all()


class TwitterBehaviorTaxonomyFilter(filters.FilterSet):
    no_parent = django_filters.BooleanFilter(name='parent_id__isnull')
    US = django_filters.BooleanFilter(name='US')
    GB = django_filters.BooleanFilter(name='GB')
    class Meta:
        model = TwitterBehaviorTaxonomy
        fields = ['US', 'GB', 'parent_id', 'no_parent']


class TwitterBehaviorTaxonomyListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterBehaviorTaxonomySerializer
    queryset = TwitterBehaviorTaxonomy.objects.order_by('name').all()
    filter_backends = (filters.DjangoFilterBackend, )
    filter_class = TwitterBehaviorTaxonomyFilter


class TwitterBehaviorFilter(filters.FilterSet):
    class Meta:
        model = TwitterBehavior
        fields = ['tw_behavior_taxonomy_id', 'country_code']


class TwitterBehaviorListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated,)
    serializer_class = TwitterBehaviorSerializer
    queryset = TwitterBehavior.objects.all()
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)
    search_fields = ('name', )
    filter_class = TwitterBehaviorFilter


class TwitterBehaviorJSONListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated, )
    def get(self, request, *args, **kwargs):
        import time
        start_time = time.time()
        code = request.query_params.get('country_code', 'US')
        behaviors = TwitterBehavior.objects_raw.filter(country_code=code).all()
        behavior_res = {}
        for b in behaviors:
            b.tw_targeting_id = str(b.tw_targeting_id)
            item = {}
            item['type'] = 'behavior'
            item['name'] = b.name
            item['parent'] = b.tw_behavior_taxonomy_id
            item['tw_targeting_id'] = b.tw_targeting_id

            _path = []
            _path.append(b.tw_behavior_taxonomy.name)
            if b.tw_behavior_taxonomy.parent:
                _path.append(b.tw_behavior_taxonomy.parent.name)
            _path.reverse()

            item['taxonomy_path'] = ': '.join(_path)

            behavior_res[b.tw_targeting_id] = item

            if b.tw_behavior_taxonomy.parent:
                #item['parents'].append(b.tw_behavior_taxonomy.parent_id)
                p_id = b.tw_behavior_taxonomy.parent_id
                p = b.tw_behavior_taxonomy.parent
                if not behavior_res.get(p_id):
                    behavior_res[p_id] = {
                        'name': p.name,
                        'type': 'taxonomy',
                        'children': [b.tw_behavior_taxonomy_id],
                        'parent': False
                    }
                else:
                    if b.tw_behavior_taxonomy_id not in behavior_res[p_id]['children']:
                        behavior_res[p_id]['children'].append(b.tw_behavior_taxonomy_id)

            if not behavior_res.get(b.tw_behavior_taxonomy_id):
                behavior_res[b.tw_behavior_taxonomy_id] = {
                    'name': b.tw_behavior_taxonomy.name,
                    'type': 'taxonomy',
                    'children': [b.tw_targeting_id],
                    'parent': b.tw_behavior_taxonomy.parent_id
                }
            else:
                if b.tw_targeting_id not in behavior_res[b.tw_behavior_taxonomy_id]['children']:
                    behavior_res[b.tw_behavior_taxonomy_id]['children'].append(b.tw_targeting_id)

        return Response(behavior_res)


class TwitterEventListView(generics.ListAPIView):
    authentication_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, settings.TW_ACCESS_TOKEN,
                        settings.TW_ACCESS_SECRET)
        account_id = TwitterAccount.objects.first().tw_account_id
        res = {}
        #try:
        resource = '/%s/targeting_criteria/events' % settings.TW_API_VERSION
        response = Request(client, 'get', resource).perform()

        if response.headers['x-rate-limit-remaining'] == "0" and settings.TW_RATE_LIMIT_ALERT:
            send_twitter_alert_email({"account_id": account_id, "endpoint": resource})

        data = response.body['data']
        for d in data:
            event_type = d['event_type']
            event_type = event_type.replace('MUSIC_AND_', '')
            event_type = event_type.replace('_', ' ').capitalize()
            if not res.get(event_type):
                res[event_type] = []
            item = {
                'name': d['name'],
                'reach': human_format(d['reach']['total_reach']),
                'id': str(base36_to_int(d['id'])),
                'start_time': d['start_time'],
                'end_time': d['end_time'],
                'is_global': d['is_global'],
                'country_code': d['country_code']
            }
            res[event_type].append(item)

        new_res = {}
        for event_type in res:
            new_res[event_type] = sorted(res[event_type], key=lambda item: item['name'])
        #res['status'] = 'ok'
        """
        except Error as e:
            res['message'] = str(e)
            res['status'] = 'fail'
        except Exception as e:
            res = {
                'status': 'fail',
                'message': str(e)
            }
        """
        return Response(new_res)