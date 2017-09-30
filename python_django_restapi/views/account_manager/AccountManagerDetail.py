from restapi.models.AccountManager import AccountManager
from restapi.serializers.AccountManagerSerializer import AccountManagerSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class AccountManagerDetail(BaseDetail):
    # Retrieve, update or delete a AccountManage instance.
    serializer_class = AccountManagerSerializer

    @property
    def queryset(self):
        return AccountManager.objects.all()
