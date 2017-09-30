from restapi.models.ManageUser import ManageUser
from restapi.serializers.ManageUserSerializer import ManageUserSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class ManageUserList(BaseListCreate):
    # List all user, or create a new ad group.
#    queryset = ManageUser.objects.all()
    serializer_class = ManageUserSerializer
    list_filter_fields = ('user_id', 'full_name',)
    contains_filter_fields = ('full_name',)
    query_filter_fields = ('full_name',)
    order_fields = ('user_id', '-user_id')

    @property
    def queryset(self):
        return ManageUser.objects.all()
