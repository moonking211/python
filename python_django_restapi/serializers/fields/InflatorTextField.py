from rest_framework import serializers
import re
from restapi.models.Source import Source


class InflatorTextField(serializers.CharField):
    def to_internal_value(self, data):
        if data:
            data = re.sub(r"[\r\n]+", "\r\n", data)
        return data

    @staticmethod
    def is_valid(inflator_text):
        if inflator_text:
            sources = [r['source'] for r in Source.objects.all().values('source')]
            sources += ['*']
            items = re.split(r'[\r\n]+', inflator_text)
            used_sources = []
            for item in items:
                if item.find(' ') == -1:
                    source = '*'
                    value = item
                else:
                    source, value = tuple(re.split(r'\s+', item, 1))
                if source not in sources:
                    return False, 'Unknown source "%s"' % source
                try:
                    float(value)
                except ValueError:
                    return False, 'Invalid format'
                if source in used_sources:
                    return False, 'Sources are not unique'
                used_sources.append(source)
        return True, ''
