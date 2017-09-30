from django.db import models

from restapi.models.base import BaseModel
from restapi.models.managers import BaseManager


class RoleManager(BaseManager):
    pass


class Role(BaseModel):
    role_id = models.AutoField(primary_key=True)
    role = models.CharField(max_length=255, blank=True)
    acl = models.TextField(blank=True)

    objects = RoleManager()
    objects_raw = models.Manager()

    def __unicode__(self):
        return self.role

    class Meta:
        managed = True
        unique_together = ('role_id', 'role')
        db_table = 'role'
        app_label = 'restapi'
