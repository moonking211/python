from django.contrib.auth.models import Group
from restapi.models.choices import STATUS_ENABLED


class UserSave(object):

    @staticmethod
    def save(request):
        user_in_groups = list(request.DATA.get('user_in_groups', []))
        groups = [int(x.pk) for x in Group.objects.filter(name__in=user_in_groups)]
        if groups:
            request.DATA['groups'] = groups
        return request
