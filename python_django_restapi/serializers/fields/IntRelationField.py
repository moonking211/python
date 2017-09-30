from rest_framework import serializers


class IntRelationField(serializers.IntegerField):
    def __init__(self, *args, **kwargs):
        self.related_model = kwargs.pop('related_model', None)
        self.allow_zero = kwargs.pop('allow_zero', False)
        super(IntRelationField, self).__init__(*args, **kwargs)

    def to_internal_value(self, value):
        if self.related_model:
            if int(value) == 0 and self.allow_zero:
                pass
            elif self.related_model.objects.filter(pk=int(value)):
                pass
            else:
                raise serializers.ValidationError('Invalid value')
        return super(IntRelationField, self).to_internal_value(value)
