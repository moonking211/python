from django.db.models import DateTimeField
from dateutil.parser import parse
from django.db.models import Q
from django.http import QueryDict
import re

from rest_framework import serializers


class FilterByListMixin(object):
    list_filter_separator = ','
    list_filter_fields = ()
    list_filter_prepare = ()  # (('field1', str), ('field2', int))

    query_filter_fields = ()

    contains_filter_fields = ()
    contains_filter_include_pk = False

    comparison_filter_fields = ()

    order_fields = ()
    order_fields_separator = ','

    specific_order_field = ()
    query_params = QueryDict('', mutable=False)

    def get_queryset(self):
        queryset = self.queryset
        self.query_params = self.query_params if self.query_params else self.request.query_params

        # list
        params = {}
        list_filter_fields = []
        for name in self.list_filter_fields:
            value = self.query_params.get(name, None)
            if value is not None and value != '':
                list_filter_fields.append(name.split('__')[0])
                values = value.split(self.list_filter_separator)
                func = dict(self.list_filter_prepare).get(name, None)
                if func is not None:
                    values = [func(v) for v in values]
                params[name] = values
        if params:
            queryset = queryset.model.objects.filter_by_list(params, queryset=queryset)

        # comparison filters like: end_date__lt
        params = {}
        for operation in ['lt', 'gt', 'lte', 'gte']:
            for name in self.comparison_filter_fields:
                key = "%s__%s" % (name, operation)
                value = self.query_params.get(key, None)
                if value is not None:
                    # pylint: disable=protected-access
                    if name in queryset.model._meta.get_all_field_names():
                        # pylint: disable=protected-access
                        field = queryset.model._meta.get_field_by_name(name)[0]
                        if isinstance(field, DateTimeField):
                            if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3}|)Z$', value):
                                raise serializers.ValidationError('Use a valid format: 0000-00-00T00:00:00Z')
                            value = parse(value)
                    params[key] = value
        if params:
            queryset = queryset.filter(**params)

        # contains (like '%value%' on exact field)
        for name in self.contains_filter_fields:
            value = self.query_params.get(name, None)
            if value is not None:
                kwargs = [{'%s__icontains' % name: value}]
                if self.contains_filter_include_pk:
                    try:
                        kwargs.append({'pk': int(value)})
                    except ValueError:
                        pass
                filter_query = [Q(**kwarg) for kwarg in kwargs]
                queryset = queryset.filter(reduce(lambda q1, q2: q1 | q2, filter_query))

        # query (like '%value%' on preset list of fields)
        query = self.query_params.get('query', None)
        if query is not None:
            kwargs = [{"%s__icontains" % f: query} for f in self.query_filter_fields]
            filter_query = [Q(**kwarg) for kwarg in kwargs]
            queryset = queryset.filter(reduce(lambda q1, q2: q1 | q2, filter_query))

        # order
        order = self.query_params.get('order', None)
        if order is not None:
            fields = [f for f in order.split(self.order_fields_separator) if f in self.order_fields]
            if fields:
                field = fields[0]
                check_field = field.split('__')[0]
                if check_field[0] == '-':
                    check_field = check_field[1:]
                queryset = queryset.order_by(field)

        # specific order
        if order is not None:
            for field, func in self.specific_order_field:
                if field == order:
                    queryset = sorted(queryset, key=func)

        return queryset
