# encoding: utf-8

from __future__ import unicode_literals

from django.conf import settings
from django.http import HttpResponse

from rest_framework import views
from rest_framework.response import Response

from restapi.models.Advertiser import Advertiser
from restapi.models.Source import Source
from restapi.models.choices import INFLATOR_SOURCES
from restapi.models.choices import IAB_CATEGORIES
from restapi.models.choices import MANAGE_CATEGORIES
from restapi.models.choices import OTHER_IAB_CATEGORIES
from restapi.models.choices import FLURRY_PERSONAS
from restapi.models.choices import FREQUENCY_SOURCES
from restapi.models.choices import COUNTRIES
from restapi.models.choices import US_REGIONS
from restapi.models.choices import US_REGION_DMA
from restapi.models.choices import CREATIVE_ATTRS
from restapi.models.choices import PLACEMENT_TYPE_CHOICES
from restapi.models.choices import SIZE_CHOICES
from restapi.registry import REGISTRY

CHOICES = (
    ('iab_classification', IAB_CATEGORIES),
    ('inflator_sources', INFLATOR_SOURCES),
    ('frequency_sources', FREQUENCY_SOURCES),
    ('manage_classification', MANAGE_CATEGORIES),
    ('other_iab_classification', OTHER_IAB_CATEGORIES),
    ('flurry_personas', FLURRY_PERSONAS),
    ('countries', COUNTRIES),
    ('usa_regions', US_REGIONS),
    ('usa_region_dma', US_REGION_DMA),
    ('placement_types', PLACEMENT_TYPE_CHOICES),
    ('creative_attrs', CREATIVE_ATTRS),
    ('sizes', SIZE_CHOICES)
)


class InitList(views.APIView):
    # pylint: disable=unused-argument,no-self-use
    def get(self, request, **unused_kwargs):
        user = REGISTRY.get('user', None)
        if not user.is_authenticated():
            return HttpResponse('{"HTTP-STATUS": 401}', status=200)
        data = {
            'username': user.username,
            'roles': user.profile.get_roles(),
            'tabs_urls': settings.TABS_URLS,
            'advertisers': {a.pk: a.advertiser for a in Advertiser.objects.own()},
            'placement_sources': {s.pk: s.source for s in Source.objects.all()},
            'osv': {'ios': settings.OSV_LATEST_IOS, 'android': settings.OSV_LATEST_ANDROID}
        }
        for name, choices in CHOICES:
            data[name] = {d[0]: d[1] for d in choices}
        return Response(data)
