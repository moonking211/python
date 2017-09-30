from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
import pytz
import requests
from restapi.models.Campaign import Campaign
from restapi.models.Io import Io
from restapi.models.TradingDesk import TradingDesk
from restapi.serializers.IoSerializer import IoSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate
from restapi.views.filters.IoCampaignFilter import IoCampaignFilter


def extend_entry_by_stats_data(ios):
    campaign_ids = set()
    all_advertiser_campaigns = dict()

    for io in ios:
        campaigns = io.get('campaigns', [])
        new_ids = [value['campaign_id'] for value in campaigns]
        if not new_ids:
            new_ids = Campaign.objects.filter(advertiser_id=io['advertiser_id']).values_list('campaign_id', flat=True)
            all_advertiser_campaigns[io['advertiser_id']] = new_ids
        campaign_ids |= set(new_ids)
    campaign_ids_str = ",".join([str(i) for i in sorted(campaign_ids)])

    # Get earliest start_date and latest end_date from all IOs
    now = datetime.now().date()
    now_date = now.strftime("%Y-%m-%d")
    start_date = None
    end_date = None
    for io in ios:
        if io['start_date']:
            io['start_date'] = io['start_date'].strftime("%Y-%m-%d")
        if io['end_date']:
            io['end_date'] = io['end_date'].strftime("%Y-%m-%d")
        if start_date is None or (io['start_date'] is not None and io['start_date'] < start_date):
            start_date = io['start_date']
        if end_date is None or (io['end_date'] is not None and io['end_date'] > end_date):
            end_date = io['end_date'] if io['end_date'] is not None else now_date
    if start_date:
        start_date = start_date
    if end_date:
        end_date = end_date

    if not end_date or end_date > now_date or end_date < start_date:
        end_date = now_date

    CACHE_TIME = 3600
    CACHE_KEY = 'io_stats_api_response_{}_{}_{}'.format(campaign_ids_str, start_date, end_date)

    stats = cache.get(CACHE_KEY)
    if not stats:
        params = ['date_from={}'.format(start_date),
                  'date_to={}'.format(end_date),
                  'filter_by_campaign_id={}'.format(campaign_ids_str),
                  'break_by=campaign,date',
                  'format=json']

        query = '&'.join(params)
        token = TradingDesk.objects.get(pk=1).trading_desk_key
        headers = {'Authorization': 'token token="%s"' % token}
        url = "".join([settings.STATS_API_DOMAIN, settings.ADVERTISER_STATS_API_PATH, '?', query])

        r = requests.get(url, headers=headers, verify=False)
        stats = sorted(r.json(), key=lambda k: (k['date'], k['campaign_id']))
        cache.set(CACHE_KEY, stats, CACHE_TIME)
    ios = sorted(ios, key=lambda k: (k['start_date'], sorted(k['campaigns'], key=lambda k: k['campaign_id'])))

    for io in ios:
        # List of campaigns names and ids for csv export
        campaign_names_list = [c['campaign'] for c in io['campaigns']]
        campaign_ids_list = [c['campaign_id'] for c in io['campaigns']]
        io['campaigns_list'] = ', '.join('{} ({})'.format(*t) for t in zip(campaign_names_list, campaign_ids_list)) \
            if len(campaign_ids_list) > 0 else "All"

        io['revenue'] = 0

    for stat in stats:
        revenue = float(stat['revenue'])
        date = stat['date']
        active_ios = []

        for io in ios:
            if len(io['campaigns']) == 0 \
                    and int(stat['campaign_id']) in all_advertiser_campaigns[io['advertiser_id']] \
                    and date >= io['start_date'] \
                    and (not io['end_date'] or date <= io['end_date']):
                active_ios.append(io)

            if int(stat['campaign_id']) in [entity['campaign_id'] for entity in io['campaigns']] \
                    and date >= io['start_date'] \
                    and (not io['end_date'] or date <= io['end_date']):
                active_ios.append(io)

        if not active_ios:
            continue

        for io in active_ios:
            if io['revenue'] >= io['io_budget']:
                continue

            elif io['revenue'] + revenue <= io['io_budget']:
                io['revenue'] += revenue
                revenue = 0
                break

            else:
                revenue -= io['io_budget'] - io['revenue']
                io['revenue'] = io['io_budget']
                continue

        if revenue:
            io['revenue'] += revenue

        # Calculate avg. revenue and over/under for eah IO
    for io in ios:
        io_start_date = io['start_date']
        io_end_date = io['end_date']
        if not io_end_date:
            io_end_date = now_date
        days = (datetime.strptime(io_end_date, "%Y-%m-%d") - datetime.strptime(io_start_date, "%Y-%m-%d")).days + 1
        io['avg_revenue'] = io['revenue'] / days if days else None
        io['over_under'] = io['revenue'] - io['io_budget']
        io['over_under_pcent'] = io['over_under'] / io['io_budget'] if io['io_budget'] else None


class IoList(BaseListCreate):
    # List all ios, or create a new io.
    serializer_class = IoSerializer
    filter_class = IoCampaignFilter
    comparison_filter_fields = ('start_date', 'end_date',)

    list_filter_fields = ('io_id',
                          'advertiser_id',
                          'campaigns')

    order_fields = ('io_id', '-io_id',
                    'advertiser_id', '-advertiser_id',
                    'io_document_link', '-io_document_link',
                    'start_date', '-start_date',
                    'end_date', '-end_date',
                    'io_budget', '-io_budget',
                    'notes', '-notes')

    @property
    def queryset(self):
        return Io.objects.all()

    def get_queryset(self):
        params = self.request.query_params
        queryset = super(IoList, self).get_queryset()
        start_date, end_date = params.get('start_date', None), params.get('end_date', None)
        order = params.get('order', None)
        io_type = params.get('io_type', None)

        utc = pytz.UTC
        today = utc.localize(datetime.now()).date()

        if io_type == 'active':
            queryset = queryset.filter(Q(end_date__gte=today) | Q(end_date__isnull=True))
        elif io_type =='expired':
            queryset = queryset.extra(where=["end_date !='0000-00-00'"]).filter(end_date__lt=today)

        if order in ['days_left', '-days_left']:
            case = 'CASE ' \
                   'WHEN io.start_date > CURDATE() OR io.end_date = "0000-00-00" THEN 3 ' \
                   'WHEN io.end_date >= CURDATE() AND io.start_date <= CURDATE() THEN 2 ' \
                   'ELSE 1 END'

            queryset = queryset.extra(select={'days_sort_field1': case,
                                              'days_sort_field2': 'DATEDIFF(io.end_date, CURDATE())'})

            order_by = ['days_sort_field1', 'days_sort_field2'] if order == 'days_left' else \
                       ['-days_sort_field1', '-days_sort_field2']

            queryset = queryset.extra(order_by=order_by)

        if start_date and end_date:
            queryset = queryset.filter((Q(start_date__gte=start_date, start_date__lte=end_date))
                                       | (Q(end_date__gte=start_date, end_date=end_date)))

        return queryset

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(IoList, self).finalize_response(request, response, *args, **kwargs)
        csv_filename = response.get('Content-Disposition', None)
        if csv_filename:
            response['Content-Disposition'] = "attachment; filename={0}".format('io-export-file.csv')
        try:
            results = response.data['results']
            if not results:
                return response
            extend_entry_by_stats_data(ios=results)
        except KeyError:
            pass
        except TypeError:
            results = response.data
            if not results:
                return response
            extend_entry_by_stats_data(ios=results)
        return response
