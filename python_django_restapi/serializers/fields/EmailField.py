from django.core.validators import validate_email
from rest_framework import serializers


class EmailField(serializers.CharField):
    def to_internal_value(self, data):
        if data:
            try:
                validate_email(data)
            except serializers.ValidationError:
                raise serializers.ValidationError({'email': 'Enter a valid email'})
        return super(EmailField, self).to_internal_value(data)
