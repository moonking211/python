from rest_framework import serializers
from restapi.models.choices import OPT_TYPE_CHOICES
from restapi.models.AdGroup import AdGroup
from restapi.models.Revmap import Revmap
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.MultipleChoiceField import MultipleChoiceField
from restapi.serializers.fields.PKRelatedField import PKRelatedField


class RevmapSerializer(BaseModelSerializer):
    ad_group_id = PKRelatedField(queryset=AdGroup.objects_raw.all())
    ad_group = serializers.CharField(required=True, allow_blank=False)
    campaign_id = serializers.IntegerField(required=True, allow_null=False)
    campaign = serializers.CharField(required=True, allow_blank=False)
    opt_type = MultipleChoiceField(choices=OPT_TYPE_CHOICES, required=False)
    opt_value = serializers.DecimalField(max_digits=9, decimal_places=4, default=0, required=False)
    rev_type = MultipleChoiceField(choices=OPT_TYPE_CHOICES, required=False)
    rev_value = serializers.DecimalField(max_digits=9, decimal_places=4, default=0, required=False)
    target_type = MultipleChoiceField(choices=OPT_TYPE_CHOICES, required=False)
    target_value = serializers.DecimalField(max_digits=9, decimal_places=4, default=0, required=False)
    last_update = DateTimeField(read_only=True)

    # pylint: disable=old-style-class
    class Meta:
        model = Revmap
