from rest_framework import serializers


class PKRelatedField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        if isinstance(value, long):
            return value
        return value.pk
