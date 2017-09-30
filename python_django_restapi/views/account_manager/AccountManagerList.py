from restapi.models.AccountManager import AccountManager
from restapi.serializers.AccountManagerSerializer import AccountManagerSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class AccountManagerList(BaseListCreate):
    # List all AccountManager, or create a new AccountManager.
    serializer_class = AccountManagerSerializer
    list_filter_fields = ('status', 'account_manager_id', 'email', 'skype',)
    contains_filter_fields = ('email',)
    contains_filter_include_pk = True
    query_filter_fields = ('account_manager_id', )
    order_fields = ('account_manager_id', '-account_manager_id')

    @property
    def queryset(self):
        return AccountManager.objects.all()
