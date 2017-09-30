from restapi.models.User import User
from restapi.views.base_view.BaseDetail import BaseDetail
from restapi.serializers.UserSerializer import UserSerializer
from restapi.views.user.UserSave import UserSave


class UserDetail(BaseDetail):
    # Retrieve, update or delete a user instance.
    serializer_class = UserSerializer

    def put(self, request, *args, **kwargs):
        return super(UserDetail, self).put(UserSave.save(request), *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super(UserDetail, self).put(UserSave.save(request), *args, **kwargs)

    @property
    def queryset(self):
        return User.objects.all()
