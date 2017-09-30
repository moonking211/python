from collections import OrderedDict
from rest_framework import serializers


class BaseReadonlySerializer(serializers.Serializer):
    required_in_schema = []
    permissions_extra_fields = []

    # pylint: disable=unused-argument
    def create(self, *args, **kwargs):
        raise Exception("%s can't create anything", self.__class__.__name__)

    # pylint: disable=unused-argument
    def update(self, *args, **kwargs):
        raise Exception("%s can't update anything", self.__class__.__name__)

    def get_fields(self):
        fields = OrderedDict()
        all_fields = super(BaseReadonlySerializer, self).get_fields()
        select_field_names = self._get_select_field_names()
        if select_field_names is not None:
            for name in select_field_names:
                fields[name] = all_fields[name]
            return fields
        return all_fields

    def _get_select_field_names(self):
        if 'request' in self.context and '$select' in self.context['request'].QUERY_PARAMS:
            names = [unicode(name.strip()) for name in self.context['request'].QUERY_PARAMS['$select'].split(',')]
            return names
        return None
