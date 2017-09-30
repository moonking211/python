from collections import OrderedDict
import json
import re
from rest_framework import serializers
from restapi.models.Ad import Ad
from restapi.models.AdGroup import AdGroup
from restapi.models.Advertiser import Advertiser
from restapi.models.Campaign import Campaign
from restapi.models.Event import Event
from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.models.TrackingProvider import TrackingProvider
from restapi.models.choices import IAB_CATEGORIES, MANAGE_CATEGORIES, OTHER_IAB_CATEGORIES
from restapi.models.choices import STATUS_CHOICES
from restapi.models.choices import STATUS_ENABLED
from restapi.models.choices import STATUS_PAUSED
from restapi.models.choices import BUDGET_TYPES_CHOICES
from restapi.registry import REGISTRY
from restapi.serializers.AdSerializer import AdSerializer
from restapi.serializers.AdGroupSerializer import AdGroupSerializer
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.DateTimeField import ZeroDateTimeField
from restapi.serializers.fields.InflatorTextField import InflatorTextField
from restapi.serializers.fields.JSONField import JSONField
from restapi.serializers.fields.MultipleChoiceField import MultipleChoiceField
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.serializers.validators.BaseValidator import BaseValidator


class TWInternalCampaignSerializer(BaseModelSerializer):
    source_type = serializers.IntegerField(required=False)
    advertiser_id = PKRelatedField(queryset=Advertiser.objects_raw.all())
    advertiser = serializers.CharField(read_only=True)

    class Meta:
        model = Campaign
        fields = ('campaign_id',
                  'campaign',
                  'advertiser_id',
                  'advertiser',
                  'source_type',
                  'status'
                  )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Campaign.objects_raw.all(),
                fields=('advertiser_id', 'campaign')
            )
        ]

    def create(self, validated_data):
        request = self.context.get('request', None)
        cpi_target_goal = request.data.get('cpi_target_goal', 0)
        validated_data['genre'] = 0
        validated_data['source_type'] = 2
        validated_data['attribution_window'] = 30
        campaign = super(TWInternalCampaignSerializer, self).create(validated_data)
        revmap = TwitterRevmap(campaign_id=campaign, opt_type='install' if cpi_target_goal else 'click',
                               opt_value=cpi_target_goal)
        revmap.save()

        event_ibid = Event(campaign_id=campaign,
                           event='i-bid',
                           description='Impression bid.',
                           default_args='',
                           base_event_id=0,
                           deleted=False,
                           max_frequency=None,
                           frequency_interval=None,
                           show_in_stats=True,
                           accept_unencrypted=False)
        event_ibid.save()

        event_impression = Event(campaign_id=campaign,
                                 event='impression',
                                 description='Ad impression.',
                                 default_args='',
                                 base_event_id=event_ibid.event_id,
                                 deleted=False,
                                 max_frequency=1,
                                 frequency_interval=86400,
                                 show_in_stats=True,
                                 accept_unencrypted=False)
        event_impression.save()

        event_click = Event(campaign_id=campaign,
                            event='click',
                            description='Ad click.',
                            default_args='',
                            base_event_id=event_impression.event_id,
                            deleted=False,
                            max_frequency=None,
                            frequency_interval=None,
                            show_in_stats=True,
                            accept_unencrypted=False)
        event_click.save()

        event_install = Event(campaign_id=campaign,
                              event='install',
                              description='App install.',
                              default_args='',
                              base_event_id=event_click.event_id,
                              deleted=False,
                              max_frequency=1,
                              frequency_interval=None,
                              show_in_stats=True,
                              accept_unencrypted=False)
        event_install.save()

        event_app_open = Event(campaign_id=campaign,
                               event='app_open',
                               description='TW App open.',
                               default_args='',
                               base_event_id=event_install.event_id,
                               deleted=False,
                               max_frequency=1,
                               frequency_interval=None,
                               show_in_stats=True,
                               accept_unencrypted=False)
        event_app_open.save()

        event_engagement = Event(campaign_id=campaign,
                                 event='engagement',
                                 description='TW Engagement.',
                                 default_args='',
                                 base_event_id=event_impression.event_id,
                                 deleted=False,
                                 max_frequency=1,
                                 frequency_interval=None,
                                 show_in_stats=True,
                                 accept_unencrypted=False)
        event_engagement.save()

        event_follow = Event(campaign_id=campaign,
                             event='follow',
                             description='TW Follow.',
                             default_args='',
                             base_event_id=event_impression.event_id,
                             deleted=False,
                             max_frequency=1,
                             frequency_interval=None,
                             show_in_stats=True,
                             accept_unencrypted=False)
        event_follow.save()

        event_reply = Event(campaign_id=campaign,
                            event='reply',
                            description='TW Reply.',
                            default_args='',
                            base_event_id=event_impression.event_id,
                            deleted=False,
                            max_frequency=1,
                            frequency_interval=None,
                            show_in_stats=True,
                            accept_unencrypted=False)
        event_reply.save()

        event_retweet = Event(campaign_id=campaign,
                              event='retweet',
                              description='TW retweet.',
                              default_args='',
                              base_event_id=event_impression.event_id,
                              deleted=False,
                              max_frequency=1,
                              frequency_interval=None,
                              show_in_stats=True,
                              accept_unencrypted=False)
        event_retweet.save()

        return campaign


class CampaignSerializer(BaseModelSerializer):
    # pylint: disable=old-style-class
    source_type = serializers.IntegerField(required=False)
    advertiser_id = PKRelatedField(queryset=Advertiser.objects_raw.all())
    advertiser = serializers.CharField(read_only=True)
    agency_id = serializers.IntegerField(read_only=True)
    agency = serializers.CharField(read_only=True)
    trading_desk_id = serializers.IntegerField(read_only=True)
    trading_desk = serializers.CharField(read_only=True)
    viewthrough_url = serializers.CharField(required=False, allow_blank=True)
    iab_classification = MultipleChoiceField(choices=IAB_CATEGORIES,
                                             validators=[BaseValidator.required_validator],
                                             required=True)
    manage_classification = MultipleChoiceField(choices=MANAGE_CATEGORIES, required=False)
    other_iab_classification = MultipleChoiceField(choices=OTHER_IAB_CATEGORIES, required=False)
    frequency_map = JSONField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    inflator_text = InflatorTextField(required=False, allow_blank=True)
    targeting = serializers.CharField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    manage_budget_type = serializers.CharField(read_only=True)
    flight_start_date = ZeroDateTimeField(required=False, allow_null=True)
    flight_end_date = ZeroDateTimeField(required=False, allow_null=True)
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=False)
    tracking_provider_id = PKRelatedField(required=False, queryset=TrackingProvider.objects_raw.all(), allow_null=True)

    daily_budget_type = ChoiceCaseInsensitiveField(choices=BUDGET_TYPES_CHOICES, required=False)
    flight_budget_type = ChoiceCaseInsensitiveField(choices=BUDGET_TYPES_CHOICES, required=False)
    last_update = DateTimeField(read_only=True)
    paused_at = DateTimeField(read_only=True)
    parent_name = serializers.CharField(read_only=True)
    agency_name = serializers.CharField(read_only=True)
    trading_desk_name = serializers.CharField(read_only=True)
    cpi_goal = serializers.SerializerMethodField()

    required_in_schema = ['status', 'app_install', 'priority']
    permissions_extra_fields = ['targeting.min_slice', 'targeting.max_slice']
    DOMAIN_MIN_LENGTH = 10

    class Meta:
        model = Campaign
        fields = ('campaign_id',
                  'campaign',
                  'source_type',
                  'advertiser_id',
                  'advertiser',
                  'agency_id',
                  'agency',
                  'trading_desk_id',
                  'trading_desk',
                  'notes',
                  'sampling_rate',
                  'throttling_rate',
                  'domain',
                  'redirect_url',
                  'destination_url',
                  'viewthrough_url',
                  'tracking_provider_id',
                  'inflator_text',
                  'frequency_map',
                  'priority',
                  'daily_budget_type',
                  'daily_budget_value',
                  'daily_spend',
                  'status',
                  'parent_name',
                  'agency_name',
                  'trading_desk_name',
                  'agency_id',
                  'trading_desk_id',
                  'distribution_app_sha1_mac',
                  'distribution_app_sha1_udid',
                  'distribution_app_sha1_android_id',
                  'distribution_app_ifa',
                  'distribution_app_md5_ifa',
                  'distribution_app_xid',
                  'distribution_web',
                  'flight_start_date',
                  'flight_end_date',
                  'flight_budget_type',
                  'flight_budget_value',
                  'attribution_window',
                  'genre',
                  'last_update',
                  'paused_at',
                  'external_id',
                  'categories',
                  'targeting',
                  'capped',
                  'iab_classification',
                  'manage_classification',
                  'other_iab_classification',
                  'manage_budget_type',
                  'total_cost_cap',
                  'daily_cost_cap',
                  'total_loss_cap',
                  'daily_loss_cap',
                  'app_install',
                  'overridden',
                  'ignore_fatigue_segment',
                  'ignore_suppression_segment',
                  'ad_groups_total',
                  'ad_groups_enabled',
                  'ads_total',
                  'ads_enabled',
                  'ads_disapproved',
                  'black_lists_total',
                  'black_lists_campaign',
                  'black_lists_ad_group',
                  'white_lists_total',
                  'white_lists_campaign',
                  'white_lists_ad_group',
                  'custom_hints_total',
                  'custom_hints_campaign',
                  'custom_hints_ad_group',
                  'discrete_pricing_total',
                  'discrete_pricing_campaign',
                  'discrete_pricing_ad_group',
                  'cpi_goal',
                  'ads_to_pause',
                  'ads_to_delete',
                  'a9_pending',
                  'a9_failed')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Campaign.objects_raw.all(),
                fields=('advertiser_id', 'campaign')
            )
        ]

    def _is_valid_frequency_map(self, errors):
        frequency_map = self.validated_data.get('frequency_map', None)

        if frequency_map:
            try:
                frequency_map_json = json.loads(frequency_map)
                if '375x50' in frequency_map_json:
                    errors['frequency_map'] = '375x50 size is currently unsupported'
            except Exception:
                pass

    def _is_valid_no_distributions(self, errors):
        # at least one Distribution must be selected
        distribution_fields = ('distribution_app_sha1_android_id',
                               'distribution_app_ifa',
                               'distribution_web')
        has_distributions = False
        for field in distribution_fields:
            has_distributions |= self.validated_data.get(field, False)

        if not has_distributions:
            errors['distributions'] = 'No distributions'

    def _is_valid_domain(self, errors):
        domain = self.validated_data.get('domain', None)
        if domain and not re.match("^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|" +
                                           "([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|" +
                                           "([a-zA-Z0-9][a-zA-Z0-9-_]{1,61}[a-zA-Z0-9]))\." +
                                           "([a-zA-Z]{2,6}|[a-zA-Z0-9-]{2,30}\.[a-zA-Z]{2,3})$", domain):
            errors['domain'] = 'should not contain http:// or https:// and must be valid url'

    def _is_valid_flight_budget_data(self, errors):
        if self.validated_data.get('flight_start_date') and self.validated_data.get('flight_end_date'):
            if self.validated_data.get('flight_start_date') > self.validated_data.get('flight_end_date'):
                errors['flight start/end dates'] = 'flight start date need to be before flight end date'
        if self.validated_data.get('daily_budget_value') or self.validated_data.get('flight_budget_value'):
            if not self.validated_data.get('flight_budget_type'):
                errors['flight budget type'] = 'You must set Flight Budget Type'
        if self.validated_data.get('flight_budget_value') or self.validated_data.get('total_cost_cap') \
                or self.validated_data.get('total_loss_cap'):
            if not self.validated_data.get('flight_start_date'):
                errors['flight start date'] = 'You must set Flight Start Date'
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

    def _is_valid_attribution_window(self, errors):
        attribution_window = self.validated_data.get('attribution_window', None)
        if attribution_window and not attribution_window >= 0:
            errors['attribution_window'] = 'Must be positive number'

    def _is_valid_app_install(self, errors):
        targeting = self.validated_data.get('targeting')
        targeting = json.loads(targeting) if targeting else {}
        destination_url = self.validated_data.get('destination_url', None)
        # AMMYM-2708
        if self.validated_data.get('app_install', None) and "os" in targeting:
            os = targeting["os"]
            if os == "iOS" and not destination_url.startswith('https://itunes.apple.com'):
                errors['destination_url'] = 'Destination URL must start w/: https://itunes.apple.com'
            if os == "Android" and not destination_url.startswith('https://play.google.com'):
                errors['destination_url'] = 'Destination URL must start w/: https://play.google.com'

    def _is_valid_urls(self, errors):
        ignore_fatigue_segment = self.validated_data.get('ignore_fatigue_segment', None)
        ignore_suppression_segment = self.validated_data.get('ignore_suppression_segment', None)
        destination_url = self.validated_data.get('destination_url', None)
        redirect_url = self.validated_data.get('redirect_url', None)
        viewthrough_url = self.validated_data.get('viewthrough_url', None)
        if viewthrough_url and viewthrough_url.find('https://') == -1:
            errors['impression url'] = 'insecure URL, use https://'
        if destination_url and len(destination_url) < self.DOMAIN_MIN_LENGTH:
            errors['destination_url'] = 'Must be at least {0} characters long'.format(self.DOMAIN_MIN_LENGTH)
        if not ignore_fatigue_segment and not ignore_suppression_segment:
            if redirect_url and redirect_url.find('https://') == -1:
                errors['click url'] = 'insecure URL, use https://'

    def _is_valid_priority(self, errors):
        if self.validated_data.get('priority'):
            if self.validated_data.get('priority') > 100 or self.validated_data.get('priority') < 0:
                errors['priority'] = 'Priority can not be less than 0 and more than 100'

    def _is_valid_genre(self, errors):
        if not self.validated_data.get('genre', None):
            errors['genre'] = 'Field is required'

    def _is_valid_app_classifications(self, errors):
        app_install = self.validated_data.get('app_install', None)
        manage_classification = self.validated_data.get('manage_classification', None)
        if app_install is True and not manage_classification:
            errors['app classifications'] = 'Field is required if app install yes'

    def _get_status(self):
        return self.validated_data.get('status', None)

    def _is_valid_inflator(self, errors):
        inflator_valid, error_message = InflatorTextField.is_valid(self.validated_data.get('inflator_text'))
        if not inflator_valid:
            errors['inflator_text'] = error_message

    def _is_valid_base(self, *args, **kwargs):
        return super(CampaignSerializer, self).is_valid(*args, **kwargs)

    def is_valid(self, *args, **kwargs):
        if not self.initial_data.get('advertiser_id', None):
            raise serializers.ValidationError({'advertiser_id': 'Field is required'})

        errors = {}
        valid = self._is_valid_base(*args, **kwargs)

        status = self._get_status()
        if status is None and self.instance:
            status = self.instance.status
        validate_only = False
        request = self.context.get('request', None)
        if request and 'validate_only' in request.query_params:
            validate_only = True

        self._is_valid_frequency_map(errors)
        self._is_valid_no_distributions(errors)
        self._is_valid_flight_budget_data(errors)
        self._is_valid_domain(errors)
        self._is_valid_app_install(errors)
        self._is_valid_urls(errors)
        self._is_valid_priority(errors)
        self._is_valid_genre(errors)
        self._is_valid_app_classifications(errors)
        self._is_valid_inflator(errors)
        self._is_valid_attribution_window(errors)

        # tracking_provider_id = self.validated_data.get('tracking_provider_id', None)
        # if app_install is True and not tracking_provider_id:
        #            errors['tracking_provider_id'] = 'Field is required if app install yes'

        if validate_only and self.instance and status in [STATUS_ENABLED, STATUS_PAUSED]:
            # check adgroups
            err = {}
            queryset = AdGroup.objects.filter(campaign_id=self.instance)
            if validate_only:
                queryset = queryset.filter(status__in=[STATUS_ENABLED, STATUS_PAUSED])
            else:
                queryset = queryset.filter(status=STATUS_ENABLED)
            for instance in queryset:
                serializer = AdGroupSerializer(data=instance.as_dict(), context=self.context, instance=instance)
                valid = serializer.is_valid(raise_exception=False, skip_ads_validation=True)
                if not valid:
                    err[instance.pk] = serializer._errors
            if err:
                errors['bad_adgroups'] = err

            # check ads
            err = {}
            queryset = Ad.objects.filter(ad_group_id__campaign_id=self.instance)
            if validate_only:
                queryset = queryset.filter(status__in=[STATUS_ENABLED, STATUS_PAUSED])
            else:
                queryset = queryset.filter(status=STATUS_ENABLED)
            for instance in queryset:
                serializer = AdSerializer(data=instance.as_dict(), context=self.context, instance=instance)
                valid = serializer.is_valid(raise_exception=False)
                if not valid:
                    err[instance.pk] = serializer._errors
            if err:
                errors['bad_ads'] = err

        if errors:
            raise serializers.ValidationError(errors)

        if valid:
            self._prepare_categories_data()

        return valid

    def _prepare_categories_data(self):
        categories = self.validated_data.pop('iab_classification', [])
        categories += self.validated_data.pop('manage_classification', [])
        categories += self.validated_data.pop('other_iab_classification', [])
        value = []
        for element in categories:
            if element not in value:
                value.append(element)
        self.validated_data['categories'] = ' '.join(value)

    def update(self, instance, *args, **kwargs):
        request = self.context.get('request', None)
        if request and 'validate_only' in request.query_params:
            return instance
        return super(CampaignSerializer, self).update(instance, *args, **kwargs)

    def create(self, *args, **kwargs):
        campaign = super(CampaignSerializer, self).create(*args, **kwargs)
        event_ibid = Event(campaign_id=campaign,
                           event='i-bid',
                           description='Impression bid.',
                           default_args='',
                           base_event_id=0,
                           deleted=False,
                           max_frequency=None,
                           frequency_interval=None,
                           show_in_stats=True,
                           accept_unencrypted=False)
        event_ibid.save()
        event_impression = Event(campaign_id=campaign,
                                 event='impression',
                                 description='Ad impression.',
                                 default_args='',
                                 base_event_id=event_ibid.event_id,
                                 deleted=False,
                                 max_frequency=1,
                                 frequency_interval=86400,
                                 show_in_stats=True,
                                 accept_unencrypted=False)
        event_impression.save()
        event_click = Event(campaign_id=campaign,
                            event='click',
                            description='Ad click.',
                            default_args='',
                            base_event_id=event_impression.event_id,
                            deleted=False,
                            max_frequency=None,
                            frequency_interval=None,
                            show_in_stats=True,
                            accept_unencrypted=False)
        event_click.save()
        event_install = Event(campaign_id=campaign,
                              event='install',
                              description='App install.',
                              default_args='',
                              base_event_id=event_click.event_id,
                              deleted=False,
                              max_frequency=1,
                              frequency_interval=None,
                              show_in_stats=True,
                              accept_unencrypted=False)
        event_install.save()
        return campaign

    def to_representation(self, instance, **kwargs):
        to_representation_dict = super(CampaignSerializer, self).to_representation(instance, **kwargs)

        user = REGISTRY.get('user', None)

        try:
            data = json.loads(to_representation_dict.get('targeting'), object_pairs_hook=OrderedDict)
            fields = ["targeting.%s" % f for f in data.keys()]
            permitted_fields = user.get_permitted_instance_fields(instance=instance, action='read', fields=fields)
            for k in data.keys():
                if "targeting.%s" % k not in permitted_fields:
                    del data[k]
        except:
            data = None

        to_representation_dict['targeting'] = '' if data is None else json.dumps(data)

        return to_representation_dict

    def get_cpi_goal(self, instance, **kwargs):
        if instance.source_type == 2:
            revmap = TwitterRevmap.objects.filter(campaign_id=instance.campaign_id).first()
            if revmap:
                return revmap.opt_value
            else:
                return ''
        else:
            return ''
