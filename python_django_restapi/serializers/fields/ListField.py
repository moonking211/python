from rest_framework import serializers


class ListField(serializers.CharField):

    def __init__(self, **kwargs):
        super(ListField, self).__init__(**kwargs)

    def to_representation(self, value):
        return value
