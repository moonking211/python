from rest_framework import serializers


class ChoiceCaseInsensitiveField(serializers.ChoiceField):
    def to_internal_value(self, data):
        for key in self.choices.keys():
            if key.lower() == data.lower():
                return key
        return super(ChoiceCaseInsensitiveField, self).to_internal_value(data)
