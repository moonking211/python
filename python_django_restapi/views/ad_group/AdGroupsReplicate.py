import json
from django.forms.models import model_to_dict
from django.db import transaction
from django.db.models import Q

from itertools import groupby

from rest_framework import permissions
from rest_framework import views
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.authentication import SessionAuthentication

from restapi.models.AdGroup import AdGroup
from restapi.models.Ad import Ad
from restapi.serializers.AdGroupSerializer import AdGroupSerializer
from restapi.serializers.AdSerializer import AdSerializer
from restapi.models.choices import STATUS_PAUSED, STATUS_ENABLED


class AdGroupsReplicate(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    # pylint: disable=no-self-use
    def post(self, request):
        data = request.DATA
        new_ad_groups = []

        try:
            new_names = data['new_names']
            src_ad_group_ids = [long(x) for x in data['src_ad_group_ids']]
            include_ads = bool(data['include_ads'])
            include_redirect_url = bool(data['include_redirect_url'])
            retain_ads_status = bool(data['retain_ads_status'])
            all_enabled_ads = bool(data['all_enabled_ads'])
            all_paused_ads = bool(data['all_paused_ads'])
        # pylint: disable=broad-except
        except Exception:
            status = HTTP_400_BAD_REQUEST
        else:
            with transaction.atomic():
                src_ad_groups_qs = AdGroup.objects.filter(pk__in=src_ad_group_ids)
                src_ad_groups = list(src_ad_groups_qs)
                ads_qs = Ad.objects.filter(Q(ad_group_id__in=src_ad_group_ids),
                                           ~Q(status__in=['deleted', 'archived']))
                ads = list(ads_qs) if include_ads else []
                grp_by_pk = dict([(k, list(v)[0]) for k, v in groupby(src_ad_groups, lambda x: x.pk)])
                ads_by_group_id = dict([(k, list(v)) for k, v in groupby(ads, lambda x: x.ad_group_id.pk)])

                for names, primary_key in zip(new_names, src_ad_group_ids):
                    src_ad_group = grp_by_pk.get(primary_key, None)
                    if src_ad_group is None:
                        continue
                    for name in names:
                        cloned_ad_group = src_ad_group.make_copy()
                        cloned_ad_group.ad_group = name

                        instance_data = model_to_dict(cloned_ad_group)

                        instance_data['frequency_map'] = json.dumps(instance_data['frequency_map'])
                        instance_data['revmap_rev_type'] = cloned_ad_group.revmap_rev_type
                        instance_data['revmap_rev_value'] = cloned_ad_group.revmap_rev_value
                        instance_data['revmap_opt_type'] = cloned_ad_group.revmap_opt_type
                        instance_data['revmap_opt_value'] = cloned_ad_group.revmap_opt_value
                        instance_data['revmap_target_type'] = cloned_ad_group.revmap_target_type
                        instance_data['revmap_target_value'] = cloned_ad_group.revmap_target_value

                        ad_group_serializer = AdGroupSerializer(data=instance_data,
                                                                context={'request': request},
                                                                instance=cloned_ad_group)
                        ad_group_serializer.is_valid(raise_exception=True)
                        ad_group_serializer.save()


                        new_ad_groups.append(cloned_ad_group.pk)
                        for src_ad in ads_by_group_id.get(primary_key, []):
                            cloned_ad = src_ad.make_copy()
                            cloned_ad.ad_group_id_id = cloned_ad_group.pk

                            if retain_ads_status:
                                cloned_ad.status = src_ad.status

                            elif all_enabled_ads:
                                cloned_ad.status = STATUS_ENABLED

                            elif all_paused_ads:
                                cloned_ad.status = STATUS_PAUSED

                            if not include_redirect_url:
                                cloned_ad.redirect_url = ''

                            ad_serializer = AdSerializer(data=model_to_dict(cloned_ad),
                                                         context={'request': request},
                                                         instance=cloned_ad)
                            ad_serializer.is_valid(raise_exception=True)
                            ad_serializer.save()

            status = HTTP_200_OK
        return Response(new_ad_groups, status=status)
