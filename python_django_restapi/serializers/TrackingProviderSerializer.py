from restapi.models.TrackingProvider import TrackingProvider
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.PKRelatedField import PKRelatedField


class TrackingProviderSerializer(BaseModelSerializer):
    tracking_provider = PKRelatedField(required=True, queryset=TrackingProvider.objects_raw.all())

    # pylint: disable=old-style-class
    class Meta:
        model = TrackingProvider
