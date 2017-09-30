from rest_framework import serializers
import re


class DefaultArgsTextField(serializers.CharField):
    def to_representation(self, value):
        return re.sub(r'[\r\n]+', '', value) if value else value
