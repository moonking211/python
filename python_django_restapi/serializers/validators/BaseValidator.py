import json
from rest_framework import serializers


class BaseValidator(object):
    @staticmethod
    # pylint: disable=invalid-name
    def JSONValidator(value):
        if value in ['""', '']:
            return
        try:
            json.loads(value)
        except ValueError:
            raise serializers.ValidationError('Invalid format')

    @staticmethod
    def required_validator(value):
        if not value:
            raise serializers.ValidationError('This field is required.')

    @staticmethod
    def is_digit_or_none(obj, field):
        return BaseValidator.__validate_digit_or_none(obj.initial_data.get(field, None))

    @staticmethod
    def is_digit_or_none_value(value):
        return BaseValidator.__validate_digit_or_none(value)

    @staticmethod
    def is_digit(value):
        return BaseValidator.__is_digit(value)

    @staticmethod
    def __is_digit(value):
        try:
            int(value)
            is_digit = True
        except ValueError:
            is_digit = False

        return is_digit

    @staticmethod
    def __validate_digit_or_none(value):
        if value is None:
            is_digit_or_none = True
        else:
            is_digit_or_none = BaseValidator.__is_digit(value)

        return is_digit_or_none
