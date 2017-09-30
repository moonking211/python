from django.db import models

from restapi.models.base import BaseModel
from restapi.models.managers import BaseManager

import restapi.audit_logger as audit
import restapi.http_caching as http_caching

AUDIT_TYPE_CURRENCY = 15


class CurrencyManager(BaseManager):
    pass


class Currency(BaseModel):
    currency_id = models.AutoField(primary_key=True)
    currency_name = models.CharField(max_length=64, default=None, null=True, blank=True)
    currency_code = models.CharField(max_length=64, default=None, null=True, blank=True)

    objects = CurrencyManager()
    objects_raw = models.Manager()
    permission_check = False

    def __unicode__(self):
        return self.currency_code

    class Meta:
        managed = True
        unique_together = ('currency_name', 'currency_code')
        db_table = 'currency'
        app_label = 'restapi'

audit.AuditLogger.register(Currency, audit_type=AUDIT_TYPE_CURRENCY, check_delete='physical_delete')
http_caching.HTTPCaching.register(Currency)
