from django.db import models

import restapi.audit_logger as audit
import restapi.http_caching as http_caching
from restapi.models.managers import BaseManager
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.fields import ZeroDateTimeField
from restapi.models.Role import Role

AUDIT_TYPE_MANAGE_USER = 1


class ManageUserManager(BaseManager):
    pass


class ManageUser(BaseModel):
    user_id = models.AutoField(primary_key=True)
    role_id = models.ForeignKey(Role, db_column='role_id')
    full_name = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)
    password_salt = models.BinaryField(max_length=16, blank=True)
    password_hash = models.BinaryField(max_length=20, blank=True)
    create_time = DateTimeField(null=True, default=None)
    last_log_in_time = ZeroDateTimeField(default=None, null=True, blank=True)

    objects = ManageUserManager()
    objects_raw = models.Manager()

    def __unicode__(self):
        return self.email

    class Meta:
        managed = True
        unique_together = ('full_name', 'email')
        db_table = 'user'
        app_label = 'restapi'

audit.AuditLogger.register(ManageUser, audit_type=AUDIT_TYPE_MANAGE_USER, check_delete='physical_delete')
http_caching.HTTPCaching.register(ManageUser)
