from rest_framework import serializers
from restapi.models.choices import OPT_TYPE_CHOICES
from restapi.models.Campaign import Campaign
from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.MultipleChoiceField import MultipleChoiceField
from restapi.serializers.fields.PKRelatedField import PKRelatedField


class TwitterRevmapSerializer(BaseModelSerializer):
    campaign_id = PKRelatedField(queryset=Campaign.objects_raw.all())
    tw_campaign_id = serializers.IntegerField()
    tw_line_item_id = serializers.IntegerField()
    opt_type = MultipleChoiceField(choices=OPT_TYPE_CHOICES, required=False)
    opt_value = serializers.DecimalField(max_digits=9, decimal_places=4, default=0, required=False)
    last_update = DateTimeField(read_only=True)

    # pylint: disable=old-style-class
    class Meta:
        model = TwitterRevmap
