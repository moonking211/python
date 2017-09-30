import decimal
from django.db import transaction
from django.db.models import Q

from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework import permissions
from rest_framework import views
from rest_framework import serializers

from datetime import datetime, date
import json

from restapi.models.AdGroup import AdGroup


class BaseBulkOperations(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)
    serializer = None
    model = None

    def post(self, request):
        data = request.DATA
        failed_objects = list()
        status = None

        delete_ids = data.get('delete', [])
        save_data = data.get('save', [])
        patch_data = data.get('patch', [])
        campaign_id = data.get('campaign_id', None)

        try:
            campaign_id = long(campaign_id) if campaign_id else None
            delete_ids = [int(pk) for pk in delete_ids]
            save_data = list(save_data)
            patch_data = list(patch_data)
        # pylint: disable=broad-except
        except Exception:
            status = HTTP_400_BAD_REQUEST
        else:
            with transaction.atomic():
                failed_objects = self.bulk_create_or_update(save_data, request, campaign_id, create=True)
                failed_objects.extend(self.bulk_create_or_update(patch_data, request, campaign_id, partial_update=True))

                if failed_objects:
                    raise serializers.ValidationError(json.dumps(failed_objects, cls=CustomJSONEncoder))

                for instance in self.model.objects.filter(pk__in=delete_ids):
                    instance.delete()
            status = HTTP_200_OK if patch_data or save_data or delete_ids else HTTP_204_NO_CONTENT

        return Response(failed_objects, status=status)

    def bulk_create_or_update(self, data_list, request, campaign_id=None, partial_update=False, create=False):
        failed_objects = list()

        if not partial_update:
            unique_together = self.get_unique_together()
            duplicate_list = []
            for i in range(len(data_list)):
                for index in range(len(data_list)-1, i, -1):
                    entry = [(f, data_list[index][f]) for f in unique_together]
                    entry_cmp = [(f, data_list[index-1][f]) for f in unique_together]

                    if cmp(entry, entry_cmp) == 0:
                        duplicate_list.append(data_list[index])
                        failed_objects.append({'Not unique entries for create': data_list[index]})

            hasher = lambda x: repr(tuple(sorted(x.items())))
            data_list = [l1 for l1 in data_list if hasher(l1) not in [hasher(l2) for l2 in duplicate_list]]

        for data_entry in data_list:
            id_value = data_entry.get('id', None)
            instance = None
            if id_value is not None:
                instance_qs = self.model.objects.filter(pk=data_entry['id'])
                instance = instance_qs.first() if instance_qs.exists() else None

            if instance is None and not create:
                instance = self.get_instance_by_unique_together(data_entry)

            if self.model == AdGroup and campaign_id is not None:
                if data_entry['campaign_id'] != str(campaign_id):
                    instance = None
                elif instance is not None \
                        and instance.campaign_id is not None \
                        and instance.campaign_id.pk != campaign_id:
                    instance.pk = None
                data_entry['campaign_id'] = campaign_id

            if instance is not None and partial_update and instance.pk is not None:
                instance_data = instance.as_dict()
                for k in instance_data:
                    value = instance_data[k]
                    if k not in data_entry:
                        # pylint: disable=unidiomatic-typecheck
                        data_entry[k] = json.dumps(value) if type(value) in [list, dict] else value
            try:
                # pylint: disable=not-callable
                serializer = self.serializer(data=data_entry, context={'request': request}, instance=instance)
                serializer.is_valid(raise_exception=True)
                serializer.save()

            # pylint: disable=broad-except
            except Exception as exception:
                msg = exception.detail if hasattr(exception, 'detail') else exception.message
                failed_objects.append({json.dumps(msg): data_entry})

        return failed_objects

    def get_instance_by_unique_together(self, data_entry):
        try:
            obj = self.model.objects.get(
                reduce(lambda q1, q2: q1 & q2, [Q(**kwarg)
                                                for kwarg in [({f: data_entry[f]}) if f in data_entry else ({f: None})
                                                              for f in self.get_unique_together()]]))
        # pylint: disable=broad-except
        except Exception:
            obj = None
        return obj if obj is not None else None

    def get_unique_together(self):
        return (list(self.model.Meta.unique_together)
                if hasattr(self.model.Meta, 'unique_together')
                else list(reduce(lambda t1, t2: t1 + t2, self.model._meta.unique_together)))


class CustomJSONEncoder(json.JSONEncoder):
    DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    DATE_FORMAT = "%Y-%m-%d"

    def default(self, obj):
        if isinstance(obj, datetime):
            if obj and obj.year <= 1000:
                obj = "1000-01-01 00:00:00"
            elif obj and obj.year >= 9000:
                obj = '9999-12-31 23:59:59'
            else:
                obj = obj.strftime(self.DATE_TIME_FORMAT)
            return obj

        elif isinstance(obj, date):
            return obj.strftime(self.DATE_FORMAT)
        elif isinstance(obj, decimal.Decimal):
            return float(obj)

        return json.JSONEncoder.default(self, obj)
