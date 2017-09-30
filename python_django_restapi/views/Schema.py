# encoding: utf-8

from __future__ import unicode_literals

from collections import OrderedDict
import json

import six

from django.core.cache import cache
from django.http import HttpResponse
from django.utils.encoding import force_text

from rest_framework import views
from rest_framework.response import Response
from rest_framework.metadata import SimpleMetadata
from rest_framework.serializers import PrimaryKeyRelatedField

from restapi.models.Advertiser import Advertiser
from restapi.models.TradingDesk import TradingDesk
from restapi.serializers.AccountManagerSerializer import AccountManagerSerializer
from restapi.serializers.AdGroupSerializer import AdGroupSerializer
from restapi.serializers.AdSerializer import AdSerializer
from restapi.serializers.AdvertiserSerializer import AdvertiserSerializer
from restapi.serializers.AgencySerializer import AgencySerializer
from restapi.serializers.AuditLogSerializer import AuditLogSerializer
from restapi.serializers.CurrencySerializer import CurrencySerializer
from restapi.serializers.UserSerializer import UserSerializer
from restapi.serializers.BidderBlacklistSerializer import BidderBlacklistSerializer
from restapi.serializers.BidderWhitelistSerializer import BidderWhitelistSerializer
from restapi.serializers.CampaignSerializer import CampaignSerializer
from restapi.serializers.CustomHintSerializer import CustomHintSerializer
from restapi.serializers.EventSerializer import EventSerializer
from restapi.serializers.RevmapSerializer import RevmapSerializer
from restapi.serializers.SearchSerializer import SearchSerializer
from restapi.serializers.SourceSerializer import SourceSerializer
from restapi.serializers.TradingDeskSerializer import TradingDeskSerializer
from restapi.serializers.ManageUserSerializer import ManageUserSerializer
from restapi.serializers.twitter.TwitterAccountSerializer import TwitterAccountSerializer
from restapi.serializers.twitter.TwitterUserSerializer import TwitterUserSerializer
from restapi.serializers.TrackingProviderSerializer import TrackingProviderSerializer
from restapi.registry import REGISTRY

CACHE_TIME = 300  # 5 minutes
CACHE = True

SERIALIZERS = (
    ('ad_group', AdGroupSerializer),
    ('ad', AdSerializer),
    ('advertiser', AdvertiserSerializer),
    ('agency', AgencySerializer),
    ('currency', CurrencySerializer),
    ('account_manager', AccountManagerSerializer),
    ('auditlog', AuditLogSerializer),
    ('user', UserSerializer),
    ('bidder_blacklist', BidderBlacklistSerializer),
    ('bidder_whitelist', BidderWhitelistSerializer),
    ('campaign', CampaignSerializer),
    ('custom_hint', CustomHintSerializer),
    ('event', EventSerializer),
    ('revmap', RevmapSerializer),
    ('search', SearchSerializer),
    ('source', SourceSerializer),
    ('trading_desk', TradingDeskSerializer),
    ('manage_user', ManageUserSerializer),
    ('tw_twitter_user', TwitterUserSerializer),
    ('tw_account', TwitterAccountSerializer),
    ('tracking_provider', TrackingProviderSerializer),
)

EXTRA_PERMISSIONS = {
    # This permissions represents platforms.
    'platforms': {
        'properties': (
            # Exchange platform.
            'exchange',
            # Twitter platform.
            'twitter'
        ),
        'actions': ()
    },
    'tops': {'properties': ('revenue', 'cost', 'profit'), 'actions': ()},
    # This permissions represents Twitter tools section.
    'tw_tools': {
        'properties': (
            # Twitter tailored audience list.
            'audience_list',
        ),
        'actions': ()
    },
    # This permissions represents Reports -> Report By Day columns.
    'report_by_day': {
        'actions': (),
        'properties': (
            'date',
            'i-bid',
            'i-bid_response',
            'impression',
            'win_rate',
            'click',
            'ctr',
            'install',
            'ir',
            'cpm',
            'rpm',
            'cpi',
            'rpi',
            'cost',
            'client_rev',
            'revenue',
            'profit',
            'margin'
        )
    },
    # This permissions represents Reports -> Report By Campaign columns.
    'report_by_campaign': {
        'actions': (),
        'properties': (
            'date',
            'campaign',
            'campaign_id',
            'i-bid',
            'i-bid_response',
            'impression',
            'win_rate',
            'click',
            'ctr',
            'install',
            'ir',
            'cpm',
            'rpm',
            'cpi',
            'rpi',
            'cost',
            'client_rev',
            'revenue',
            'profit',
            'margin'
        )
    },
    'metrics': {
        'properties': (
            'revenue',
            'profit',
            'margin',
            'impression',
            'click',
            'install',
            'cpm',
            'rpm',
            'cost',
            'client_rev',
            'i-bid'
        ),
        'actions': ()
    },
    # This permissions represents Navigation items.
    'navigation': {
        'actions': (),
        'properties': (
            'dashboard',
            # Trading desks
            'trading_desks__create',
            'trading_desks__list',
            # Agencies
            'agencies__create',
            'agencies__list',
            # Advertisers
            'advertisers__create',
            'advertisers__list',
            'advertisers__io_tracking_list',
            # Campaigns
            'campaigns__create',
            'campaigns__list',
            # Reports
            'reports__today_stats',
            'reports__report_by_day',
            'reports__report_by_advertiser',
            'reports__report_by_campaign',
            'reports__report_by_ad_group',
            'reports__report_by_ad',
            'reports__custom_reports',
            'reports__no_bid_reason_report',
            # Tools
            'tools__placement_tools',
            'tools__disapproved_a9_ads_tool',
            'tools__disapproved_adx_ads_tool',
            'tools__adx_creative_resubmission',
            'tools__ads_pruning',
            'tools__download_device_ids',
            'tools__advertiser_bidder_insight',
            'tools__publisher_bidder_insight',
            'tools__base_config_settings',
            'tools__tw_discovery',
            # User
            'user__create',
            'user__list',
            'user__audit_logs',
            # Twitter tools
            'tw_tools__audience_manager'
        )
    },
    'tools': {
        'properties': (
            'placements',
            'disapproved',
            'pruning',
            'resubmission',
            'device_id',
            'advertiser_bidder_insight',
            'publisher_bidder_insight',
            'show_config'
        ),
        'actions': ()
    },
    'reports': {
        'properties': (
            'today_stats',
            'report_by_day',
            'report_by_advertiser',
            'report_by_campaign',
            'report_by_ad_group',
            'report_by_ad',
            'custom_reports',
            'no_bid_reason_report'
        ),
        'actions': ()
    }
}

TD_GROUPS = (
    (21, 'Trading Desk Stakeholder'),
    (22, 'Trading Desk Campaign Supervisor'),
    (23, 'Trading Desk Campaign Manager'),
    (24, 'Trading Desk Account Manager')
)

MANAGE_GROUPS = (
    (25, 'Manage Stakeholder'),
    (26, 'Manage Super User'),
    (27, 'Manage AdOps Head'),
    (28, 'Manage AdOps Supervisor'),
    (29, 'Manage AdOps CM'),
    (30, 'Manage Account Manager'),
    (31, 'Manage TD Account Manager'),
    (32, 'Manage Creative Approval')
)

ALL_GROUPS = TD_GROUPS + MANAGE_GROUPS

DEBUG_SERIALIZER = None


class Schema(views.APIView):
    # pylint: disable=unused-argument,no-self-use
    def get(self, request, **kwargs):
        user = REGISTRY.get('user', None)
        if not user.is_authenticated():
            return HttpResponse('{"HTTP-STATUS": 401}', status=200)

        CACHE_KEY = "restapi:%s:/schema" % user.pk
        metadata = cache.get(CACHE_KEY)
        if CACHE and metadata:
            return Response(metadata)

        simple_meta = SimpleMetadata()
        metadata = OrderedDict()

        for name, cls in SERIALIZERS:
            if DEBUG_SERIALIZER and DEBUG_SERIALIZER != name:
                continue

            serializer = cls(context={'request': request})

            info = OrderedDict()
            for field_name, field in serializer.fields.items():
                field_info = OrderedDict()
                field_info['type'] = simple_meta.label_lookup[field]
                if getattr(field, 'required', False) or field_name in serializer.required_in_schema:
                    field_info['required'] = True
                attrs = ['read_only', 'label', 'help_text', 'min_length', 'max_length', 'min_value', 'max_value']

                for attr in attrs:
                    value = getattr(field, attr, None)
                    if value is not None and value is not False and value != '':
                        field_info[attr] = force_text(value, strings_only=True)

                if isinstance(field, PrimaryKeyRelatedField):
                    field_info['relation'] = self.relation_name_lookup(field.queryset.model)

                elif hasattr(field, 'choices'):
                    choices = []
                    field_info['choices'] = choices
                    data = ALL_GROUPS if name == 'user' else field.choices.items()
                    for choice_value, choice_name in data:
                        choices.append({
                            'value': choice_value,
                            'display_name': force_text(choice_name, strings_only=True)
                        })
                    if name == 'user':
                        field_info['manage_choices'] = []
                        for choice_value, choice_name in MANAGE_GROUPS:
                            field_info['manage_choices'].append({
                                'value': choice_value,
                                'display_name': force_text(choice_name, strings_only=True)
                            })

                        field_info['td_choices'] = []
                        for choice_value, choice_name in TD_GROUPS:
                            field_info['td_choices'].append({
                                'value': choice_value,
                                'display_name': force_text(choice_name, strings_only=True)
                            })
                info[field_name] = field_info

            primary_key = None
            unique_keys = []
            if hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'model'):
                model_meta = serializer.Meta.model._meta
                primary_key = model_meta.pk.name
                unique_keys = model_meta.unique_together

            metadata[name] = OrderedDict()
            metadata[name]['type'] = 'object'
            metadata[name]['primary_key'] = primary_key
            metadata[name]['unique_keys'] = unique_keys
            metadata[name]['properties'] = info

            cache.set(CACHE_KEY, metadata, CACHE_TIME)

        return Response(metadata)

    def relation_name_lookup(self, model):
        rel_name = None
        for name, serializer in SERIALIZERS:
            if hasattr(serializer, 'Meta') and serializer.Meta.model == model:
                rel_name = name
                break
        return rel_name


class Perm(views.APIView):
    """This class defines Permission endpoint (/perm)."""

    def get(self, request, **unused_kwargs):
        user = REGISTRY.get('user', None)
        if not user.is_authenticated():
            return HttpResponse(json.dumps({'HTTP-STATUS': 401}), status=401)

        cache_key = 'restapi:%s:/perm' % user.pk
        response = cache.get(cache_key)
        if CACHE and response:
            return Response(response)

        permissions = OrderedDict()

        for name, cls in SERIALIZERS:
            if DEBUG_SERIALIZER and DEBUG_SERIALIZER != name:
                continue

            serializer = cls(context={'request': request})

            fields = serializer.fields.keys()
            fields += cls.permissions_extra_fields

            if hasattr(cls, 'Meta') and getattr(cls.Meta.model, 'permission_check', False):
                model = cls.Meta.model
                permissions[name] = self.resource_permissions(user, model, True, fields, getattr(model, 'actions', []))

        for resource, data in six.iteritems(EXTRA_PERMISSIONS):
            permissions[resource] = self.resource_permissions(user, resource, True, data['properties'], data['actions'])

        profile = OrderedDict()

        trading_desks = list(TradingDesk.objects_raw.filter(trading_desk_userprofiles__user=user).values(
            'trading_desk_id',
            'trading_desk'
        )[:1])
        if trading_desks:
            profile.update(trading_desks[0])

        advertisers = list(Advertiser.objects_raw.filter(advertiser_userprofiles__user=user).values(
            'advertiser_id',
            'advertiser'
        )[:1])
        if advertisers:
            profile.update(advertisers[0])

        response = OrderedDict(
            username=user.username,
            is_manage_user=user.is_manage_user,
            profile=profile,
            roles=user.profile.get_roles(),
            permissions=permissions
        )

        cache.set(cache_key, response, CACHE_TIME)

        return Response(response)

    def resource_permissions(self, user, model, enabled, fields, model_actions):
        can_model_create = can_model_read = can_model_update = can_model_delete = can_read = can_update = True
        actions = model_actions

        can_read_fields, can_update_fields = [], []
        if enabled:
            can_model_create = bool(user.check_model_permission(model=model, action='create'))

            can_read = can_model_read = bool(user.check_model_permission(model=model, action='read'))
            if can_model_read:
                can_read_fields = user.get_permitted_model_fields(model=model, action='read', fields=fields)

            can_update = can_model_update = bool(user.check_model_permission(model=model, action='update'))
            if can_model_update:
                can_update_fields = user.get_permitted_model_fields(model=model, action='update', fields=fields)

            can_model_delete = bool(user.check_model_permission(model=model, action='delete'))

            actions = user.get_permitted_model_fields(model=model, action='action', fields=model_actions)

        info = OrderedDict()
        for field_name in fields:
            info[field_name] = OrderedDict(
                read=field_name in can_read_fields if enabled else can_read,
                update=field_name in can_update_fields if enabled else can_update
            )

        return OrderedDict(
            create=can_model_create,
            read=can_model_read,
            update=can_model_update,
            delete=can_model_delete,
            actions=actions,
            properties=info
        )
