import re
from math import ceil
from sys import maxint
from rest_framework import pagination
from rest_framework.response import Response
from restapi.models.Agency import Agency
from restapi.models.TradingDesk import TradingDesk
from restapi.models.AdGroup import AdGroup
from restapi.models.Campaign import Campaign
from restapi.models.Advertiser import Advertiser


class ListPagination(pagination.PageNumberPagination):
    page_size_query_param = '$page_size'
    CSV_FORMAT = 'csv'

    def get_paginated_response(self, data):
        params = self.request.query_params
        format_value = params.get('format', '').lower()
        page_size = self.get_page_size(self.request)
        count = ceil(self.page.paginator.count / float(page_size))

        if format_value == self.CSV_FORMAT:
            headers = dict()
            headers['Content-type'] = 'text/csv; charset=utf-8'
            headers['Content-Disposition'] = 'attachment; filename='+self._get_name(params)
            response = Response(data, headers=headers)
        else:
            response = Response({
                'count': count,
                'total': self.page.paginator.count,
                'results': data
            })

        return response

    def get_page_size(self, request):
        if self.page_size_query_param:
            if self.page_size_query_param in request.query_params:
                page_size = int(request.query_params[self.page_size_query_param])
                if page_size == 0:
                    return maxint
        return super(ListPagination, self).get_page_size(request)

    # pylint: disable=no-self-use
    def _get_name(self, params):
        campaign_id = params.get('campaign_id', None)
        ad_group_id = params.get('ad_group_id', None)
        advertiser_id = params.get('advertiser_id', None)
        trading_desk_id = params.get('trading_desk_id', None)
        advertisers = params.get('advertisers', None)
        agencies = params.get('agencies', None)
        agency_id = params.get('agency_id', None)
        trading_desks = params.get('trading_desks', None)

        name = 'export-file.csv'
        sep = '__'
        extension = '.csv'
        if campaign_id is not None:
            campaign = Campaign.objects.filter(pk=campaign_id)
            if campaign.exists():
                obj = campaign.first()
                name = sep.join([obj.campaign, str(obj.campaign_id)])+extension

        elif ad_group_id is not None:
            ad_group = AdGroup.objects.filter(pk=ad_group_id)
            if ad_group.exists():
                obj = ad_group.first()
                name = sep.join([obj.campaign_id.campaign,
                                 str(obj.campaign_id.campaign_id),
                                 obj.ad_group,
                                 str(obj.ad_group_id)])+extension

        elif advertiser_id is not None:
            advertiser = Advertiser.objects.filter(pk=advertiser_id)
            if advertiser.exists():
                obj = advertiser.first()
                name = sep.join([obj.advertiser, str(obj.advertiser_id)])+extension

        elif advertisers:
            agency_name = 'All'
            trading_desk_name = 'All'
            agency = Agency.objects.filter(agency_id=agency_id)

            if agency.exists():
                obj = agency.first()
                agency_name = obj.agency
                trading_desk_name = self.__trading_desk_name(obj.trading_desk_id_id)

            name = sep.join([trading_desk_name, agency_name, 'Advertisers_List'])+extension

        elif agencies:
            trading_desk_name = self.__trading_desk_name(trading_desk_id)
            name = sep.join([trading_desk_name, 'Agencies_List'])+extension

        elif trading_desks:
            name = 'TradingDesk_List.csv'

        return re.sub(',', '-', "_".join(name.split()))

    def __trading_desk_name(self, trading_desk_id):
        name = 'All'
        if trading_desk_id is not None:
            trading_desk = TradingDesk.objects.filter(pk=trading_desk_id)
            if trading_desk.exists():
                name = trading_desk.first().trading_desk
        return name
