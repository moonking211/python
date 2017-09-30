from collections import OrderedDict
import json
from rest_framework import serializers
from restapi.models.Campaign import Campaign
from restapi.models.AdGroup import AdGroup
from restapi.models.Ad import Ad
from restapi.models.choices import BUDGET_TYPES_CHOICES, OS_CHOICES
from restapi.models.choices import OPT_TYPE_CHOICES
from restapi.models.choices import STATUS_CHOICES
from restapi.models.choices import STATUS_ENABLED
from restapi.models.choices import STATUS_PAUSED
from restapi.registry import REGISTRY
from restapi.serializers.AdSerializer import AdSerializer
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.DateTimeField import ZeroDateTimeField
from restapi.serializers.fields.InflatorTextField import InflatorTextField
from restapi.serializers.fields.JSONField import JSONField
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.serializers.validators.BaseValidator import BaseValidator
from restapi.models.DiscretePricing import DiscretePricing, DiscretePricingIds


class AdGroupSerializer(BaseModelSerializer):
    # pylint: disable=old-style-class
    campaign_id = PKRelatedField(queryset=Campaign.objects_raw.all())
    campaign = serializers.CharField(read_only=True)
    advertiser_id = serializers.IntegerField(read_only=True)
    advertiser = serializers.CharField(read_only=True)
    agency_id = serializers.IntegerField(read_only=True)
    agency = serializers.CharField(read_only=True)
    trading_desk_id = serializers.IntegerField(read_only=True)
    trading_desk = serializers.CharField(read_only=True)
    destination_url = serializers.CharField(required=False, allow_blank=True)
    viewthrough_url = serializers.CharField(required=False, allow_blank=True)
    app_install = serializers.BooleanField(read_only=True)
    frequency_map = JSONField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    inflator_text = InflatorTextField(required=False, allow_blank=False)
    targeting = serializers.CharField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    event_args = serializers.CharField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    flight_start_date = ZeroDateTimeField(required=False, allow_null=True)
    flight_end_date = ZeroDateTimeField(required=False, allow_null=True)
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=False)
    daily_budget_type = ChoiceCaseInsensitiveField(choices=BUDGET_TYPES_CHOICES, required=False)
    flight_budget_type = ChoiceCaseInsensitiveField(choices=BUDGET_TYPES_CHOICES, required=False)
    last_update = DateTimeField(read_only=True)
    paused_at = DateTimeField(read_only=True)

    parent_name = serializers.CharField(read_only=True)

    revmap_rev_type = ChoiceCaseInsensitiveField(choices=OPT_TYPE_CHOICES, required=False)
    revmap_rev_value = serializers.DecimalField(max_digits=9, decimal_places=4, default=0, required=False)
    revmap_opt_type = ChoiceCaseInsensitiveField(choices=OPT_TYPE_CHOICES, required=False)
    revmap_opt_value = serializers.DecimalField(max_digits=9, decimal_places=4, default=0, required=False)

    required_in_schema = ['priority']
    permissions_extra_fields = ['targeting.state', 'targeting.city', 'targeting.zip_code', 'targeting.min_slice', 'targeting.max_slice']

    DOMAIN_MIN_LENGTH = 10

    class Meta:
        model = AdGroup
        fields = ('ad_group_id',
                  'campaign_id',
                  'campaign',
                  'advertiser_id',
                  'advertiser',
                  'agency_id',
                  'agency',
                  'trading_desk_id',
                  'trading_desk',
                  'app_install',
                  'frequency_map',
                  'inflator_text',
                  'targeting',
                  'event_args',
                  'flight_start_date',
                  'flight_end_date',
                  'parent_name',
                  'ad_group',
                  'ad_group_type',
                  'categories',
                  'domain',
                  'notes',
                  'redirect_url',
                  'destination_url',
                  'viewthrough_url',
                  'revmap_rev_type',
                  'revmap_rev_value',
                  'revmap_opt_type',
                  'revmap_opt_value',
                  'priority',
                  'daily_budget_type',
                  'daily_budget_value',
                  'daily_spend',
                  'capped',
                  'hourly_capped',
                  'status',
                  'tag',
                  'flight_budget_type',
                  'flight_budget_value',
                  'sampling_rate',
                  'throttling_rate',
                  'max_frequency',
                  'frequency_interval',
                  'bidder_args',
                  'last_update',
                  'paused_at',
                  'distribution_app_sha1_android_id',
                  'distribution_app_ifa',
                  'distribution_web',
                  'total_cost_cap',
                  'daily_cost_cap',
                  'total_loss_cap',
                  'daily_loss_cap',
                  'overridden',
                  'ignore_fatigue_segment',
                  'ignore_suppression_segment',
                  'ads_enabled',
                  'ads_disapproved',
                  'ads_total',
                  'black_lists_total',
                  'white_lists_total',
                  'custom_hints_total',
                  'discrete_pricing_total',
                  'ads_to_delete',
                  'ads_to_pause',
                  'a9_pending',
                  'a9_failed')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=AdGroup.objects_raw.all(),
                fields=('campaign_id', 'ad_group')
            )
        ]

    def _is_valid_frequency_map_375x50_is_not_supported(self, errors):
        frequency_map = self.validated_data.get('frequency_map', None)
        if frequency_map:
            try:
                frequency_map_json = json.loads(frequency_map)
                if '375x50' in frequency_map_json:
                    errors['frequency_map'] = '375x50 size is currently unsupported'
            except Exception:
                pass

    def _is_valid_no_distributions(self, errors):
        distribution_fields = ('distribution_app_sha1_android_id',
                               'distribution_app_ifa',
                               'distribution_web')

        distribution_values = [self.validated_data.get(field, None) for field in distribution_fields if self.validated_data.get(field, None) != None]
        if distribution_values and (True not in distribution_values):
            errors['distributions'] = 'No distributions'

    def _is_valid_rev_value_negative(self, errors):
        revmap_rev_value = self.validated_data.get('revmap_rev_value', None)
        flighting_budget_fields = ('daily_budget_value',
                                   'flight_budget_value',
                                   'total_cost_cap',
                                   'total_loss_cap',
                                   'daily_cost_cap',
                                   'daily_loss_cap')

        flighting_budget_values = {field: self.validated_data.get(field, None) >= 0  for field in flighting_budget_fields}
        for k, v in flighting_budget_values.items():
            if not v:
                errors[k] = 'Must be positive number'

        if revmap_rev_value and float(revmap_rev_value) < 0:
            errors['revmap_rev_value'] = 'Rev value could not be negative'

    def _is_valid_insecure_url(self, errors):
        redirect_url = self.validated_data.get('redirect_url', None)
        viewthrough_url = self.validated_data.get('viewthrough_url', None)
        ignore_fatigue_segment = self.validated_data.get('ignore_fatigue_segment', None)
        ignore_suppression_segment = self.validated_data.get('ignore_suppression_segment', None)

        if not ignore_fatigue_segment and not ignore_suppression_segment:
            if redirect_url and redirect_url.find('https://') == -1:
                errors['redirect_url'] = 'insecure URL, use https://'

        if viewthrough_url and viewthrough_url.find('https://') == -1:
            errors['impression url'] = 'insecure URL, use https://'

    def _is_valid_destination_url(self, errors):
        destination_url = self.validated_data.get('destination_url', None)
        if destination_url and len(destination_url) < self.DOMAIN_MIN_LENGTH:
            errors['destination_url'] = 'Must be at least {0} characters long'.format(self.DOMAIN_MIN_LENGTH)

    def _is_valid_different_segments(self, errors):
        ignore_fatigue_segment = self.validated_data.get('ignore_fatigue_segment', None)
        ignore_suppression_segment = self.validated_data.get('ignore_suppression_segment', None)

        if ignore_fatigue_segment != ignore_suppression_segment:
            errors['ignore_fatigue_segment'] = 'ignore_fatigue_segment should be the same as ignore_suppression_segment'
            errors['ignore_suppression_segment'] = 'ignore_fatigue_segment should be the same as ignore_suppression_segment'

    def _is_valid_targeting(self, errors):
        destination_url = self.validated_data.get('destination_url', None)

        targeting = self.validated_data.get('targeting')
        targeting = json.loads(targeting) if targeting else {}

        ignore_fatigue_segment = self.validated_data.get('ignore_fatigue_segment', None)
        ignore_suppression_segment = self.validated_data.get('ignore_suppression_segment', None)

        campaign = self.validated_data.get('campaign_id')
        app_install = campaign.app_install
        parent_targeting = json.loads(campaign.targeting) if campaign and campaign.targeting else {}
 
        if not parent_targeting.get('country', False):
            if not targeting.get('country', False):
                errors['country'] = 'You must set County'

        if not parent_targeting.get('os', False) and not targeting.get('os', False):
            errors['os'] = "OS must be defined in its or Parent's entity targeting"

        if parent_targeting.get('os', False) == OS_CHOICES[0][0] or targeting.get('os', False) == OS_CHOICES[0][0]:
            if not parent_targeting.get('model', False) and not targeting.get('model', False):
                errors['model'] = 'You must set Model of your device'

        if parent_targeting.get('os', False) == OS_CHOICES[0][0] or targeting.get('os', False) == OS_CHOICES[0][0]:
            if self.validated_data.get('distribution_app_sha1_android_id', False) == True:
                errors['distribution_app_sha1_android_id'] = 'Cant be selected if os = iOS'

        if parent_targeting.get('os', False) == OS_CHOICES[1][0] or targeting.get('os', False) == OS_CHOICES[1][0]:
            if self.validated_data.get('distribution_app_ifa', False) == True:
                errors['distribution_app_ifa'] = 'Cant be selected if os = Android'

        if parent_targeting.get('os', False) == OS_CHOICES[2][0] or targeting.get('os', False) == OS_CHOICES[2][0]:
            if self.validated_data.get('distribution_app_ifa', False) == True:
                errors['distribution_app_ifa'] = 'Cant be selected if os = Kindle'

        if app_install and not ignore_fatigue_segment and not ignore_suppression_segment:
            if destination_url and "os" in parent_targeting:
                os = parent_targeting["os"]
                if os == "iOS" and not destination_url.startswith('https://itunes.apple.com'):
                    errors['destination_url'] = 'Destination URL must start w/: https://itunes.apple.com'
                if os == "Android" and not destination_url.startswith('https://play.google.com'):
                    errors['destination_url'] = 'Destination URL must start w/: https://play.google.com'

    def _is_valid_flightings(self, errors):
        if self.validated_data.get('flight_start_date') and self.validated_data.get('flight_end_date'):
            if self.validated_data.get('flight_start_date') > self.validated_data.get('flight_end_date'):
                errors['flight_start_date'] = 'flight start date need to be before flight end date'

        if self.validated_data.get('priority'):
            if self.validated_data.get('priority') > 100 or self.validated_data.get('priority') < 0:
                errors['priority'] = 'Priority can not be less than 0 and more than 100'

        if self.validated_data.get('daily_budget_value') or self.validated_data.get('flight_budget_value'):
            if not self.validated_data.get('flight_budget_type'):
                errors['flight_budget_type'] = 'You must set Flight Budget Type'

        if self.validated_data.get('flight_budget_value') or self.validated_data.get('total_cost_cap') or self.validated_data.get('total_loss_cap') :
            if not self.validated_data.get('flight_start_date'):
                errors['flight_start_date'] = 'You must set Flight Start Date'

    def _is_valid_inflator(self, errors):
        (inflator_valid, error_message) = InflatorTextField.is_valid(self.validated_data.get('inflator_text'))
        if not inflator_valid:
            errors['inflator_text'] = error_message

    def _get_status(self):
        return self.validated_data.get('status', None)

    def _get_campaign_id(self):
        return self.validated_data.get('campaign_id')

    def _is_valid_base(self, *args, **kwargs):
        return super(AdGroupSerializer, self).is_valid(*args, **kwargs)

    def is_valid(self, *args, **kwargs):
        skip_ads_validation = kwargs.pop('skip_ads_validation', False)
        raise_exception = kwargs.pop('raise_exception', True)
        valid = self._is_valid_base(*args, **kwargs)
        if not valid:
            if raise_exception:
                raise serializers.ValidationError(self.errors)
            else:
                self._errors = self.errors
            return False
        errors = {}

        campaign = self._get_campaign_id()
        status = self._get_status()
        if status is None and self.instance:
            status = self.instance.status

        validate_only = False
        request = self.context.get('request', None)
        if request and 'validate_only' in request.query_params:
            validate_only = True

        self._is_valid_frequency_map_375x50_is_not_supported(errors)
        self._is_valid_no_distributions(errors)
        self._is_valid_rev_value_negative(errors)
        self._is_valid_insecure_url(errors)
        self._is_valid_destination_url(errors)
        self._is_valid_different_segments(errors)
        self._is_valid_targeting(errors)
        self._is_valid_flightings(errors)
        self._is_valid_inflator(errors)

        if valid \
                and not skip_ads_validation \
                and validate_only \
                and self.instance \
                and status in [STATUS_ENABLED, STATUS_PAUSED] \
                and campaign.status in [STATUS_ENABLED, STATUS_PAUSED]:

            err = {}
            queryset = Ad.objects.filter(ad_group_id=self.instance)
            if validate_only:
                queryset = queryset.filter(status__in=[STATUS_ENABLED, STATUS_PAUSED])
            else:
                queryset = queryset.filter(status=STATUS_ENABLED)
            for instance in queryset:
                serializer = AdSerializer(data=instance.as_dict(), context=self.context, instance=instance)
                valid =  serializer.is_valid(raise_exception=False)
                if not valid:
                    err[instance.pk] = serializer._errors
            if err:
                errors['bad_ads'] = err

        if errors:
            if raise_exception:
                raise serializers.ValidationError(errors)
            else:
                self._errors = errors
                valid = False

        return valid

    def to_representation(self, instance, **kwargs):
        to_representation_dict = super(AdGroupSerializer, self).to_representation(instance, **kwargs)

        user = REGISTRY.get('user', None)

        try:
            data = json.loads(to_representation_dict.get('targeting'), object_pairs_hook=OrderedDict)
        except:
            data = None
        else:
            fields = ["targeting.%s" % f for f in data.keys()]
            permitted_fields = user.get_permitted_instance_fields(instance=instance, action='read', fields=fields)

            for k in data.keys():
                if "targeting.%s" % k not in permitted_fields:
                    del data[k]

        to_representation_dict['targeting'] = '' if data is None else json.dumps(data)

        return to_representation_dict

    def update(self, instance, *args, **kwargs):
        request = self.context.get('request', None)
        if request and 'validate_only' in request.query_params:
            return instance

        if self.validated_data.get('revmap_rev_type', None) not in ['install', 'click']:
            objs = DiscretePricingIds.objects.filter(ad_group_id=instance.pk)
            for obj in objs:
                obj.delete()

        return super(AdGroupSerializer, self).update(instance, *args, **kwargs)
