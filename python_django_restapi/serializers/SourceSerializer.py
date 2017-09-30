from rest_framework import serializers
from restapi.models.choices import CLASS_CHOICES
from restapi.models.Source import Source
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.MultipleChoiceField import MultipleChoiceField


class SourceSerializer(BaseModelSerializer):
    source = serializers.CharField(required=True, allow_blank=False, read_only=False)
    class_value = MultipleChoiceField(required=False, choices=CLASS_CHOICES, read_only=False)

    # pylint: disable=old-style-class
    class Meta:
        model = Source
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Source.objects_raw.all(),
                fields=('source',)
            )
        ]
