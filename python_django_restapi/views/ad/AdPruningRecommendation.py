# encoding: utf-8
"""This module defines API for getting list of ads for pruning."""

from __future__ import unicode_literals

import datetime
import json
import six

from django.db import models
from django.db import transaction

from rest_framework import generics
from rest_framework import response
from rest_framework import serializers
from rest_framework import status

from restapi.models import Ad
from restapi.models import AuditLog
from restapi.models import choices
from restapi.models import CreativePruning

DELETE = 'delete'
PAUSE = 'pause'

_COLUMNS = (
    'action',
    'ad_id',
    'ad_id__ad',
    'ad_id__size',
    'ipm_rank',
    'impression_rank',
    'install_rank',
    'ctr',
    'ir',
    'rpm',
    'ppm',
    'ibid',
    'impression',
    'click',
    'install',
    'cost',
    'revenue',
    'profit',
    'margin',
    'days',
    'days_w_impression',
    'ad_id__ad_group_id',
    'ad_id__ad_group_id__ad_group',
    'ad_id__ad_group_id__campaign_id',
    'ad_id__ad_group_id__campaign_id__campaign',
    'ad_id__ad_group_id__campaign_id__advertiser_id',
    'ad_id__ad_group_id__campaign_id__advertiser_id__advertiser',
)

_COLUMN_BY_FIELD = {c.split('__')[-1]: c for c in _COLUMNS}
_ORDER_FIELDS = [c.split('__')[-1] for c in _COLUMNS] + ['-{}'.format(c) for c in _COLUMNS]
_ORDER_FIELDS.extend(['-{}'.format(c) for c in _ORDER_FIELDS])
_ORDER_FIELDS = tuple(_ORDER_FIELDS)


class AdsPruningSerializer(serializers.Serializer):
    """Serializer class for ads recommended for pruning."""
    action = serializers.CharField(required=False)
    ad_id = serializers.IntegerField(required=False)
    ad = serializers.CharField(source='ad_id__ad', required=False)
    size = serializers.CharField(source='ad_id__size', required=False)
    ipm_rank = serializers.FloatField(required=False)
    impression_rank = serializers.FloatField(required=False)
    install_rank = serializers.FloatField(required=False)
    ctr = serializers.FloatField(required=False)
    ir = serializers.FloatField(required=False)
    rpm = serializers.FloatField(required=False)
    ppm = serializers.FloatField(required=False)
    ibid = serializers.FloatField(required=False)
    impression = serializers.FloatField(required=False)
    click = serializers.FloatField(required=False)
    install = serializers.FloatField(required=False)
    cost = serializers.FloatField(required=False)
    revenue = serializers.FloatField(required=False)
    profit = serializers.FloatField(required=False)
    margin = serializers.FloatField(required=False)
    days = serializers.IntegerField(required=False)
    html = serializers.CharField(source='ad_id__html', required=False)
    days_w_impression = serializers.IntegerField(required=False)
    ad_group_id = serializers.IntegerField(source='ad_id__ad_group_id', required=False)
    ad_group = serializers.CharField(source='ad_id__ad_group_id__ad_group', required=False)
    campaign_id = serializers.IntegerField(source='ad_id__ad_group_id__campaign_id', required=False)
    campaign = serializers.CharField(source='ad_id__ad_group_id__campaign_id__campaign', required=False)
    advertiser_id = serializers.IntegerField(source='ad_id__ad_group_id__campaign_id__advertiser_id', required=False)
    advertiser = serializers.CharField(source='ad_id__ad_group_id__campaign_id__advertiser_id__advertiser',
                                       required=False)


def is_int(v):
    """Returns True if a given value can be converted to int."""
    try:
        int(v)
    except (TypeError, ValueError):
        return False
    return True


def make_query_filters(prefix, field, query_value):
    qs = [models.Q(**{'{}__{}__icontains'.format(prefix, field): query_value})]
    if is_int(query_value):
        qs.append(models.Q(**{'{}__pk'.format(prefix): query_value}))
    return reduce(lambda q, q1: q | q1, qs)


class AdsPruningUpdateSerializer(serializers.Serializer):
    # Whether to prune all ads or not.
    all = serializers.BooleanField(default=False)
    # A list of ads ids to update.
    ads = serializers.ListField(required=False)
    # A list of ads to don't update.
    skip_ads = serializers.ListField(required=False)
    # Parameters to filter ads.
    params = serializers.DictField(required=False)


class AdPruningRecommendation(generics.CreateAPIView, generics.ListAPIView):
    """API for managing ad pruning recommendations."""
    queryset = CreativePruning.CreativePruning.objects.all().select_related(
        'ad_id',
        'ad_id__ad_group_id',
        'ad_id__ad_group_id__campaign_id',
        'ad_id__ad_group_id__campaign_id__advertiser_id'
    )
    serializer_class = AdsPruningSerializer
    list_filter_fields = ('active',)
    order_fields = _ORDER_FIELDS

    _DATA_DIFF_JSON_TEMPLATE = json.dumps({'status': '%s', 'last_update': '%s'})

    def get_queryset(self):
        queryset = self.queryset

        advertiser = self.request.query_params.get('advertiser', None)
        if advertiser:
            queryset = queryset.filter(
                make_query_filters('ad_id__ad_group_id__campaign_id__advertiser_id', 'advertiser', advertiser)
            )
        advertiser_id = self.request.query_params.get('advertiser_id', None)
        if advertiser_id:
            queryset = queryset.filter(ad_id__ad_group_id__campaign_id__advertiser_id__pk=advertiser_id)

        campaign = self.request.query_params.get('campaign', None)
        if campaign:
            queryset = queryset.filter(make_query_filters('ad_id__ad_group_id__campaign_id', 'campaign', campaign))
        campaign_id = self.request.query_params.get('campaign_id', None)
        if campaign_id:
            queryset = queryset.filter(ad_id__ad_group_id__campaign_id__pk=campaign_id)

        ad_group = self.request.query_params.get('ad_group', None)
        if ad_group:
            queryset = queryset.filter(make_query_filters('ad_id__ad_group_id', 'ad_group', ad_group))
        ad_group_id = self.request.query_params.get('ad_group_id', None)
        if ad_group_id:
            queryset = queryset.filter(ad_id__ad_group_id__pk=ad_group_id)

        action = self.request.query_params.get('action', None)
        if action:
            queryset = queryset.filter(action=action)

        distinct = 'distinct' in self.request.query_params
        if distinct:
            queryset = queryset.distinct()

        order = self.request.query_params.get('order', None)
        if order:
            prefix, field = ('-', order[1:]) if order.startswith('-') else ('', order)
            if field in _COLUMN_BY_FIELD:
                queryset = queryset.order_by('{}{}'.format(prefix, _COLUMN_BY_FIELD[field]))

        columns = _COLUMNS + ('ad_id__html',)
        select = self.request.query_params.get('$select', None)
        if select:
            select = set([_COLUMN_BY_FIELD[s] for s in (s.strip() for s in select.split(','))
                          if s and s in _COLUMN_BY_FIELD])
            columns = tuple(set(columns) & select)

        return queryset.values(*columns)

    def create(self, request):
        """Prunes (updates status) ads with a given request parameters."""
        serializer = AdsPruningUpdateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        all = request.data.get('all') or False
        ads_id = [ad_id for ad_id in (request.data.get('ads') or []) if is_int(ad_id)]
        skip_ads_id = [ad_id for ad_id in (request.data.get('skip_ads') or []) if is_int(ad_id)]
        params = {_COLUMN_BY_FIELD[k]: v for k, v in six.iteritems(request.data.get('params') or {})
                  if k in _COLUMN_BY_FIELD}
        query = CreativePruning.CreativePruning.objects_raw.all()
        if all and params:
            query = query.filter(**params)
            if skip_ads_id:
                query = query.exclude(ad_id__in=skip_ads_id)
        elif ads_id:
            query = query.filter(ad_id__in=ads_id)
        else:
            return response.Response(status=status.HTTP_202_ACCEPTED)

        utc_now = datetime.datetime.utcnow()
        with transaction.atomic():
            archive_ad_ids, pause_ad_ids, new_status_by_ad_id = [], [], {}
            for ad_id, action in query.values_list('ad_id', 'action'):
                if action == DELETE:
                    new_status_by_ad_id[ad_id] = choices.STATUS_ARCHIVED
                    archive_ad_ids.append(ad_id)
                else:
                    new_status_by_ad_id[ad_id] = choices.STATUS_PAUSED
                    pause_ad_ids.append(ad_id)

            old_status__last_update_by_ad_id = {}
            ad_query = Ad.Ad.objects_raw.filter(ad_id__in=new_status_by_ad_id).values_list(
                'ad_id',
                'status',
                'last_update'
            )
            for ad_id, old_status, last_update in ad_query:
                old_status__last_update_by_ad_id[ad_id] = (old_status, last_update)

            # Set status to archived of ad pruning recommendations with action delete.
            if archive_ad_ids:
                Ad.Ad.objects_raw.filter(ad_id__in=archive_ad_ids).update(
                    status=choices.STATUS_ARCHIVED,
                    last_update=utc_now
                )

            # Set status to paused of ad pruning recommendations with action pause.
            if pause_ad_ids:
                Ad.Ad.objects_raw.filter(ad_id__in=pause_ad_ids).update(
                    status=choices.STATUS_PAUSED,
                    last_update=utc_now
                )

            # Populate audit log with ads that were modified.
            log_records, new_last_update = [], str(utc_now)
            new_data_cache = {
                choices.STATUS_ARCHIVED: self._DATA_DIFF_JSON_TEMPLATE % (choices.STATUS_ARCHIVED, new_last_update),
                choices.STATUS_PAUSED: self._DATA_DIFF_JSON_TEMPLATE % (choices.STATUS_PAUSED, new_last_update),
            }
            for ad_id, new_status in six.iteritems(new_status_by_ad_id):
                old_status, last_update = old_status__last_update_by_ad_id.get(ad_id)
                if old_status and old_status != new_status:
                    log_records.append(AuditLog.AuditLog(
                        user_id=request.user.user_id,
                        audit_type=Ad.AUDIT_TYPE_AD,
                        audit_action=AuditLog.AUDIT_ACTION_UPDATE,
                        old_data=self._DATA_DIFF_JSON_TEMPLATE % (old_status, str(last_update)),
                        new_data=new_data_cache[new_status],
                        item_id=ad_id,
                        created=utc_now
                    ))
            AuditLog.AuditLog.objects_raw.bulk_create(log_records)

            # Now we can delete selected ad pruning recommendations.
            query.delete()

        return response.Response(status=status.HTTP_202_ACCEPTED, data={
            'archived': len(archive_ad_ids),
            'paused': len(pause_ad_ids)
        })
