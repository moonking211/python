from collections import OrderedDict
import json
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

import re

from rest_framework import serializers
from django.conf import settings

from restapi.models.choices import STATUS_CHOICES
from restapi.models.choices import AD_TYPE_CHOICES
from restapi.models.choices import STATUS_ENABLED
from restapi.models.choices import STATUS_PAUSED
from restapi.models.choices import AD_TYPE_NONE
from restapi.models.choices import AD_TYPE_VIDEO
from restapi.models.choices import AD_TYPE_MRAID
from restapi.models.choices import AD_TYPE_NATIVE
from restapi.models.choices import AD_TYPE_RICHMEDIA
from restapi.models.choices import CREATIVE_ATTRS_EXPANDABLE
from restapi.models.choices import CREATIVE_ATTRS_VIDEO_AUTO_PLAY
from restapi.models.choices import CREATIVE_ATTRS_USER_INTERACTIVE
from restapi.models.AdGroup import AdGroup
from restapi.models.Ad import Ad
from restapi.registry import REGISTRY
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.InflatorTextField import InflatorTextField
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.validators.BaseValidator import BaseValidator
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.serializers.fields.DateTimeField import DateTimeField
from urlparse import urlparse
from restapi.views.Blobs import Blobs


class AdSerializer(BaseModelSerializer):
    # pylint: disable=old-style-class
    ad_group_id = PKRelatedField(queryset=AdGroup.objects_raw.all())
    ad_group = serializers.CharField(read_only=True)
    campaign_id = serializers.IntegerField(required=False, read_only=True)
    campaign = serializers.CharField(read_only=True)
    advertiser_id = serializers.IntegerField(required=False, read_only=True)
    advertiser = serializers.CharField(read_only=True)
    agency_id = serializers.IntegerField(read_only=True)
    agency = serializers.CharField(read_only=True)
    trading_desk_id = serializers.IntegerField(read_only=True)
    trading_desk = serializers.CharField(read_only=True)
    ad_type = serializers.IntegerField(max_value=256, min_value=0, required=True)
    encrypted_ad_id = serializers.CharField(required=False, read_only=True)
    bid = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=True)
    inflator_text = InflatorTextField(required=False, allow_blank=False, default='* 1.00')
    last_update = DateTimeField(read_only=True)
    created_time = DateTimeField(read_only=True)
    targeting = serializers.CharField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)

    class Meta:
        model = Ad
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Ad.objects_raw.all(),
                fields=('ad_group_id', 'ad')
            )
        ]

    def is_valid(self, *args, **kwargs):
        errors = {}
        valid = super(AdSerializer, self).is_valid(*args, **kwargs)
        raise_exception = kwargs.pop('raise_exception', True)
        ad_type = self.validated_data.get('ad_type', None)
        attrs = self.validated_data.get('attrs', None)
        i_url = self.validated_data.get('i_url', None)
        redirect_url = self.validated_data.get('redirect_url', None)
        ad_group = self.validated_data.get('ad_group_id')
        size = self.validated_data.get('size', None)
        bid = self.validated_data.get('bid', None)
        status = self.validated_data.get('status')
        external_args = self.validated_data.get('external_args', '')
        html = self.validated_data.get('html', '')
        validate_only = False
        request = self.context.get('request', None)
        if request and 'validate_only' in request.query_params:
            validate_only = True

        if size and size == '375x50':
            errors['size'] = '375x50 size is currently unsupported'

        if ad_group.revmap_rev_type == "impression" and bid is None:
            errors['bid'] = 'This field is requeired'

        if not BaseValidator.is_digit_or_none_value(ad_type):
            errors['ad_type'] = 'Field ad_type should be numbers'

        if int(ad_type) not in [choice[0] for choice in AD_TYPE_CHOICES]:
            errors['ad_type'] = 'Invalid ad_type'

        if int(ad_type) == AD_TYPE_MRAID or int(ad_type) == AD_TYPE_NATIVE:
            if not html:
                errors['html'] = 'HTML should not be empty'

        if ad_type is not None and int(ad_type) == AD_TYPE_VIDEO:
            if attrs is None or \
                    (CREATIVE_ATTRS_VIDEO_AUTO_PLAY not in
                         [int(x) for x in attrs.split(' ') if x and BaseValidator.is_digit_or_none_value(x)]):
                errors['attrs'] = 'For VIDEO ad type creative attributes ' \
                                  'should contain 6 (In-Banner Video Ad (Auto Play))'

        if ad_type is not None and (int(ad_type) == AD_TYPE_MRAID or int(ad_type) == AD_TYPE_RICHMEDIA):
            if i_url is None or not i_url:
                errors['i_url'] = 'For MRAID or RICHMEDIA types i_url field should not be empty'

            else:
                try:
                    URLValidator().__call__(i_url)
                except ValidationError:
                    errors['i_url'] = 'Incorrect i_url field format: %s' % i_url

        if ad_type is not None and int(ad_type) == AD_TYPE_NATIVE:
            if size != '0x0':
                errors['i_url'] = 'For NATIVE type the only "0x0" size is permitted'

        if redirect_url and redirect_url.find('https://') == -1:
            errors['redirect_url'] = 'Invalid value for click url: insecure URL'

        if html.find('http://') != -1:
            errors['html'] = 'Invalid value: insecure URL'

        if status == STATUS_ENABLED and not redirect_url and not ad_group.redirect_url and not ad_group.campaign_id.redirect_url:
            errors['redirect_url'] = 'Field is required. You could specify it on Campaign, Ad Group or Ad level'

        if int(ad_type) == AD_TYPE_MRAID:
            try:
                external_args_json = json.loads(external_args)
                mraid_type = external_args_json.get('mraid_type', None)
            except ValueError:
                errors['external_args'] = 'Invalid value'
            else:
                if mraid_type:
                    attrs_list = [int(x) for x in attrs.split(' ') if x and BaseValidator.is_digit_or_none_value(x)]

                    if mraid_type == 'MRAID Video' and (CREATIVE_ATTRS_VIDEO_AUTO_PLAY not in attrs_list):
                        errors['attrs'] = 'For VIDEO ad type creative attributes ' \
                                          'should contain 6 (In-Banner Video Ad (Auto Play))'

                    if mraid_type == 'MRAID Playable' and (CREATIVE_ATTRS_USER_INTERACTIVE not in attrs_list):
                        errors['attrs'] = 'For MRAID Playable ad type creative attributes ' \
                                          'should contain 13 (User Interactive (e.g., Embedded Games))'

                    if (mraid_type == 'Expandable Display'
                        or mraid_type == 'Expandable Playable'
                        or mraid_type == 'Expandable Video') and (CREATIVE_ATTRS_EXPANDABLE not in attrs_list):
                        errors['attrs'] = 'For MRAID {0} ad type creative attributes ' \
                                          'should contain 4 (Expandable (User Initiated - Click))'.format(mraid_type)
                else:
                    errors['external_args'] = "mraid_type and other required parameters should be specified. " \
                                              "Beware, HTML will be updated according to them " \
                                              "after Ad is re-saved via UI"

        if ad_type == AD_TYPE_NATIVE:
            headline = None
            try:
                external_args_json = json.loads(external_args)
                headline = external_args_json.get('headline', None)
            except ValueError:
                errors['external_args'] = 'Invalid value'
            else:
                if headline is None:
                    errors['external_args'] = 'Headline is required'
                elif not headline:
                    errors['external_args'] = 'Headline is invalid'

        if status == STATUS_ENABLED or status == STATUS_ENABLED and self.instance:
            external_args_json = None
            vast_media_file = None
            vast_duration = None
            if external_args.strip():
                try:
                    external_args_json = json.loads(external_args)
                except ValueError:
                    errors['external_args'] = 'Invalid JSON'
                else:
                    vast_media_file = external_args_json.get("vast_media_file", None)
                    vast_duration = external_args_json.get("vast_duration", None)

            if ad_type == AD_TYPE_NONE:
                errors['ad_type'] = 'Invalid value'
            elif ad_type == AD_TYPE_VIDEO:
                if not vast_media_file or not vast_duration:
                    errors['external_args'] = 'vast_media_file and vast_duration must be defined in external_args (VAST)'
            else:
                if vast_media_file or vast_duration:
                    errors['external_args'] = 'vast_media_file and vast_duration should not be defined in external_args (VAST)'

            if ad_type == AD_TYPE_NATIVE and not external_args:
                errors['external_args'] = 'This filed is required (NATIVE)'

            if ad_type != AD_TYPE_RICHMEDIA and ad_type != AD_TYPE_MRAID and ad_type != AD_TYPE_NATIVE:
                result = re.search(r'\bsrc="(.*?)"', html)
                if not result:
                    errors['html'] = 'Invalid value: No url'
                else:
                    html_link = result.group(1)
                    url_obj = urlparse(html_link)
                    result = re.search(r'\.[^\/]+', url_obj.path)
                    if not result:
                        errors['html'] = 'Invalid value: no extension'

            if external_args.find('http://') != -1:
                errors['external_args'] = 'Invalid value: insecure URL'

#            if not redirect_url and not ad_group.redirect_url and not ad_group.campaign_id.redirect_url:
#                errors['redirect_url'] = 'Redirect_url must be defined at least on one of campaign, ad_group or ad levels'

        inflator_valid, error_message = InflatorTextField.is_valid(self.validated_data.get('inflator_text'))
        if not inflator_valid:
            errors['inflator_text'] = error_message

        if errors:
            if raise_exception:
                raise serializers.ValidationError(errors)
            else:
                self._errors = errors
                valid = False

        return valid

    def to_representation(self, instance, **kwargs):
        to_representation_dict = super(AdSerializer, self).to_representation(instance, **kwargs)

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

    def create(self, validated_data):
        data_path_list = self.initial_data.get('data_path_list', None)
        if validated_data['ad_type'] == AD_TYPE_MRAID and data_path_list:
            for item in data_path_list:
                if settings.MNG_CDN is None:
                    new_path, old_path = urlparse(item['new_path']).path[1:], urlparse(item['old_path']).path[1:]
                else:
                    new_path, old_path = item['new_path'].replace(settings.MNG_CDN, ''), item['old_path'].replace(
                        settings.MNG_CDN, '')
                Blobs._move_data(new_path, old_path)
        # BUG(AMMYM-3399): When creating a new Native Ad we should always set iURL. If user did not enter a valid iURL,
        # we should get it from external args "mainimage".
        if validated_data['ad_type'] == AD_TYPE_NATIVE and not validated_data.get('i_url'):
            try:
                external_args = json.loads(validated_data['external_args'])
            except (TypeError, ValueError):
                external_args = None
            if external_args and external_args.get('mainimage'):
                validated_data['i_url'] = external_args['mainimage']
        return super(AdSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        data_path_list = self.initial_data.get('data_path_list', None)
        if validated_data['ad_type'] == AD_TYPE_MRAID and data_path_list:
            for item in data_path_list:
                if settings.MNG_CDN is None:
                    new_path, old_path = urlparse(item['new_path']).path[1:], urlparse(item['old_path']).path[1:]
                else:
                    new_path, old_path = item['new_path'].replace(settings.MNG_CDN, ''), item['old_path'].replace(
                        settings.MNG_CDN, '')
                Blobs._move_data(new_path, old_path)
        return super(AdSerializer, self).update(instance, validated_data)
