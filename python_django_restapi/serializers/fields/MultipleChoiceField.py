from rest_framework import serializers


class MultipleChoiceField(serializers.MultipleChoiceField):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return data
