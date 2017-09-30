from mng.commons.crypto import decrypt
from collections import OrderedDict
from math import ceil
import re

from rest_framework import generics
from rest_framework import permissions
from rest_framework import views
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from restapi.serializers.SearchSerializer import SearchSerializer
from restapi.models.Advertiser import Advertiser
from restapi.models.Campaign import Campaign
from restapi.models.AdGroup import AdGroup
from restapi.models.Ad import Ad
from restapi.models.Event import Event
from restapi.models.Agency import Agency
from restapi.models.twitter.TwitterCampaign import TwitterCampaign
from restapi.models.twitter.TwitterLineItem import TwitterLineItem

class InvalidValueException(APIException):
    status_code = 400
    default_detail = 'Minimum value length: 3 chars or 1 digitrs.'


class BaseSearchMixin(object):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)
    models = (Advertiser, Campaign, AdGroup, Ad, Event, Agency, TwitterCampaign, TwitterLineItem)

    def get_models(self):
        levels = self.request.query_params.get('levels', None)
        if levels is not None:
            values = levels.split(',')
            # pylint: disable=protected-access
            models = [m for m in self.models if m._meta.model_name in values]
        else:
            models = list(self.models)
        return models

    def get_value(self):
        value = self.request.query_params.get('value', None)
        is_number = re.match(r'^\d+$', value)
        if len(value) < 1 or (not is_number and len(value) < 3):
            raise InvalidValueException

        if not is_number:
            try:
                encrypted_value = decrypt(str(value))
                value = encrypted_value if encrypted_value else value
            # pylint: disable=broad-except
            except Exception:
                pass

        return value

    def search_data(self, limit=None, exclude_archived=False):
        models = self.get_models()
        value = self.get_value()
        data = OrderedDict()
        for model in models:
            # pylint: disable=protected-access
            name = model._meta.model_name
            if not self.is_status_field_exist(model):
                exclude_archived = False

            search_results = model.objects.search(value, exclude_archived=exclude_archived).order_by('-last_update')
            if limit is not None:
                search_results = search_results[:limit]
            data[name] = [r.search_result for r in search_results]
        return data

    # pylint: disable=no-self-use
    def is_status_field_exist(self, model):
        sts = 'status'
        # pylint: disable=protected-access
        field_names = [f.name for f in model._meta.fields]
        property_names = [field_name for field_name in dir(model) if isinstance(getattr(model, field_name), property)]
        return sts in field_names and sts in property_names


class Search(BaseSearchMixin, generics.ListAPIView):
    serializer_class = SearchSerializer

    def get_queryset(self):
        data = self.search_data()
        data = reduce(lambda a, b: a+b, data.values())
        data = sorted(data, cmp=Search.cmp_by_nested_ids)
        return data

    @staticmethod
    def cmp_by_nested_ids(left, right):
        for field in ['agency_id', 'advertiser_id', 'campaign_id', 'ad_group_id', 'ad_id', 'event_id']:
            if field not in left:
                return -1
            if field not in right:
                return 1
            if left[field] < right[field]:
                return -1
            if left[field] > right[field]:
                return 1
        return 0


class SearchLive(BaseSearchMixin, views.APIView):
    serializer_class = SearchSerializer

    # pylint: disable=unused-argument
    def get(self, request, **kwargs):
        group_into = int(self.request.query_params.get('group_into', 12))
        data = self.search_data(limit=group_into+1, exclude_archived=True)
        models = self.get_models()
        sizes = {}
        total = 0
        for model in models:
            # pylint: disable=protected-access
            name = model._meta.model_name
            sizes[name] = len(data[name])
            total += sizes[name]

        total_length_counter = group_into
        models_counter = len(models)
        for k in sorted(sizes, key=lambda a: sizes[a]):
            max_len = int(ceil(total_length_counter / float(models_counter)))
            if sizes[k] > max_len:
                sizes[k] = max_len
            models_counter -= 1
            total_length_counter -= sizes[k]
            data[k] = data[k][: int(sizes[k])]

        data = reduce(lambda a, b: a+b, data.values())
        return Response({'results': data, 'total': total})
