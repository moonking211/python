from rest_framework import serializers
from restapi.models.choices import SIZE_ALL


class MultipleSizeChoiceField(serializers.CharField):
    choices = []

    def __init__(self, **kwargs):
        self.choices = kwargs.pop('choices', [])
        super(MultipleSizeChoiceField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        result_list = set()
        is_all_present = False
        choices = [key for key, display_value in self.choices]

        for value in [x for x in data.split(',') if x]:
            processed_value = value.lower().strip()
            if processed_value in choices:
                if processed_value == SIZE_ALL:
                    is_all_present = True
                result_list.add(processed_value)
            else:
                raise serializers.ValidationError(('Invalid value %s'% (processed_value)))

        return ','.join(map(str, result_list)) if not is_all_present else SIZE_ALL