from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from restapi.models.User import User
from restapi.serializers.UserSerializer import UserSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate
from restapi.views.user.UserSave import UserSave

from django.http import QueryDict


class UserList(BaseListCreate):
    serializer_class = UserSerializer
    list_filter_fields = \
        ('groups__name', 'user_id', 'is_staff', 'is_active', 'date_joined', 'profile__trading_desk__trading_desk_id')
    contains_filter_fields = ('username', 'first_name', 'last_name', 'email')
    query_filter_fields = ('first_name', 'last_name', 'username', 'email')
    order_fields = ('first_name', '-first_name',
                    'last_name', '-last_name',
                    'username', '-username',
                    'email', '-email',
                    'user_id', '-user_id')

    def post(self, request, *args, **kwargs):
        return super(UserList, self).post(UserSave.save(request), *args, **kwargs)

    @property
    def queryset(self):
        return User.objects.all()

    def get_queryset(self):
        params = self.request.query_params
        trading_desk_id = params.get('trading_desk_id')
        group_id = params.get('group_id')
        is_active = params.get('is_active')
        is_staff = params.get('is_staff')

        query_params = QueryDict('', mutable=True)
        query_params.update(params)

        if trading_desk_id is not None:
            query_params['profile__trading_desk__trading_desk_id'] = trading_desk_id

        if is_active is not None:
            if 'false' == is_active:
                query_params['is_active'] = ''
            elif 'all' == is_active:
                query_params.pop('is_active')

        if is_staff is not None and 'false' == is_staff:
            query_params['is_staff'] = ''

        if group_id is not None:
            try:
                group_name = Group.objects.get(pk=int(group_id)).name
            except ObjectDoesNotExist:
                group_name = None

            query_params['groups__name'] = group_name

        self.query_params = query_params

        return super(UserList, self).get_queryset()
