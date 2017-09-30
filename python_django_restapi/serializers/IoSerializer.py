from copy import deepcopy
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from rest_framework import serializers
from restapi.models.Advertiser import Advertiser
from restapi.models.Campaign import Campaign
from restapi.models.Io import Io, Io_campaign
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.ZeroDateField import ZeroDateField
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.views.filters.IoCampaignFilter import IoCampaignFilter


class CampainIdSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Io_campaign
        fields = ('campaign_id', 'campaign')


class IoSerializer(BaseModelSerializer):
    # pylint: disable=old-style-class
    advertiser_id = PKRelatedField(queryset=Advertiser.objects_raw.all())
    campaigns = CampainIdSerialiser(required=False, many=True)
    start_date = ZeroDateField(required=True, allow_null=False)
    end_date = ZeroDateField(required=False, allow_null=True)

    # pylint: disable=old-style-class
    class Meta:
        model = Io
        filter_class = IoCampaignFilter
        fields = (
            'io_id',
            'advertiser_id',
            'agency_id',
            'trading_desk_id',
            'advertiser',
            'start_date',
            'end_date',
            'days_left',
            'campaigns',
            'io_budget',
            'io_document_link',
            'notes',
            'today_date'
        )

    def is_valid(self, *args, **kwargs):
        errors = {}
        valid = super(IoSerializer, self).is_valid(*args, **kwargs)
        start_date = self.initial_data.get('start_date', None)
        end_date = self.initial_data.get('end_date', None)
        io_document_link = self.initial_data.get('io_document_link', None)

        if io_document_link:
            try:
                URLValidator().__call__(io_document_link)
            except ValidationError:
                errors['Io Document Link'] = 'Incorrect Io Document Link URL format: {0}'.format(io_document_link)

        if start_date and end_date:
            if start_date > end_date:
                errors['Error'] = 'End Date cannot be lower than Start Date'

        if errors:
            raise serializers.ValidationError(errors)

        return valid

    def create(self, validated_data):
        campaigns_data = validated_data.pop('campaigns', None)
        from restapi.audit_logger import AuditLogger
        AuditLogger.skip_next_write = True
        io = Io.objects.create(**validated_data)
        if campaigns_data:
            for campaign_data in campaigns_data:
                Io_campaign.objects.create(io_id=io, **campaign_data)
        io.save()
        return io

    @transaction.atomic
    def update(self, instance, validated_data):
        from restapi.audit_logger import AuditLogger
        data = deepcopy(validated_data)
        validated_data.pop('campaigns', None)
        AuditLogger.skip_next_write = True
        instance = super(IoSerializer, self).update(instance, validated_data)
        if 'campaigns' in data:
            self._update_campaigns(instance, data)
        instance.save()
        return instance

    def _update_campaigns(self, instance, validated_data):
        campaigns = self.initial_data.get('campaigns')
        if isinstance(campaigns, list) and len(campaigns) >= 1:
            campaigns_data = Campaign.objects.filter(
                campaign_id__in=[campaign['campaign_id'] for campaign in campaigns]
            )
            Io_campaign.objects.filter(io_id=instance).delete()
            for campaign_data in campaigns_data:
                Io_campaign.objects.create(io_id=instance, campaign_id=campaign_data)

        if len(campaigns) == 0:
            Io_campaign.objects.filter(io_id=instance).delete()

        return instance
