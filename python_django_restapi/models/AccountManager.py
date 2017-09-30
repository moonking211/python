from django.db import models

from restapi.models.base import BaseModel
import restapi.audit_logger as audit
from restapi.models.managers import BaseManager
import restapi.http_caching as http_caching

AUDIT_TYPE_ACCOUNT_MANAGER = 14


class AccountManagerManager(BaseManager):
    pass


class AccountManager(BaseModel):
    account_manager_id = models.AutoField(primary_key=True)
    status = models.BooleanField(default=False, blank=True)
    photo_140x140 = models.BinaryField()
    first_name = models.CharField(max_length=50, default='', blank=True)
    last_name = models.CharField(max_length=50, default='', blank=True)
    title = models.CharField(max_length=50, default='', blank=True)
    email = models.CharField(max_length=50, default='', blank=True)
    phone_landline = models.CharField(max_length=15, null=True, default=None, blank=True)
    phone_mobile = models.CharField(max_length=15, null=True, default=None, blank=True)
    skype = models.CharField(max_length=50, null=True, default=None, blank=True)
    chat = models.CharField(max_length=50, null=True, default=None, blank=True)

    objects = AccountManagerManager()
    objects_raw = models.Manager()

    permission_check = False

    def __unicode__(self):
        return self.email

    class Meta:
        managed = True
        unique_together = ('email', 'first_name', 'last_name', 'title')
        db_table = 'account_manager'
        app_label = 'restapi'
        ordering = ['account_manager_id']

audit.AuditLogger.register(AccountManager, audit_type=AUDIT_TYPE_ACCOUNT_MANAGER, check_delete='physical_delete')
http_caching.HTTPCaching.register(AccountManager)
