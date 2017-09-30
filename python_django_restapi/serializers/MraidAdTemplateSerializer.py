from rest_framework import serializers
from restapi.models.MraidAdTemplate import MraidAdTemplate
from restapi.serializers.BaseModelSerializer import BaseModelSerializer


class MraidAdTemplateSerializer(BaseModelSerializer):

    # pylint: disable=old-style-class
    class Meta:
        model = MraidAdTemplate
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=MraidAdTemplate.objects_raw.all(),
                fields=('template_name', 'js_tag_version')
            )
        ]
        fields = (
            'mraid_template_id',
            'template_name',
            'js_tag_version',
            'banner_tag_version',
            'template'
        )
