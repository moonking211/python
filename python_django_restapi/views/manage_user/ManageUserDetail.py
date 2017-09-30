from restapi.models.ManageUser import ManageUser
from restapi.views.base_view.BaseDetail import BaseDetail
from restapi.serializers.ManageUserSerializer import ManageUserSerializer


class ManageUserDetail(BaseDetail):
    # Retrieve, update or delete a user instance.
#    queryset = ManageUser.objects.all()
    serializer_class = ManageUserSerializer

    @property
    def queryset(self):
        return ManageUser.objects.all()
