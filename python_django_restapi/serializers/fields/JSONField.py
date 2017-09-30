import json
from rest_framework import serializers


class JSONField(serializers.CharField):
    def to_representation(self, value):
        return value if value == '' else json.dumps(value)
