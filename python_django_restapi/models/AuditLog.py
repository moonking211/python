from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from datetime import datetime, timedelta

import json

from restapi.models.base import BaseModel
from restapi.models.base import PermissionDeniedException
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager
from restapi.time_shifting import PacificTimeShift
from restapi.registry import REGISTRY


AUDIT_ACTION_ADD = 1
AUDIT_ACTION_UPDATE = 2
AUDIT_ACTION_DELETE = 3


class AuditLogManager(BaseManager):
    def own(self, queryset=None):
        from restapi.models.User import User
        from restapi.audit_logger import AuditLogger

        # filter by user
        queryset = super(AuditLogManager, self).own(queryset)
        own_users = User.objects.filter(profile__trading_desk__trading_desk_userprofiles__user=REGISTRY['user'])
        queryset = queryset.filter(user__in=own_users)

        return queryset


class AuditLog(BaseModel):
    audit_log_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='djangouser', db_constraint=False)
    audit_type = models.IntegerField()
    audit_action = models.IntegerField()
    item_id = models.IntegerField()
    old_data = models.TextField(blank=True)
    new_data = models.TextField(blank=True)
    created = DateTimeField(null=True, default=None, auto_now_add=True)

    objects = AuditLogManager()
    objects_raw = models.Manager()
    permission_check = True

    def is_own(self):
        from restapi.models.User import User
        own_users = list(User.objects_raw.filter(profile__trading_desk__trading_desk_userprofiles__user=REGISTRY['user']))
        value = False
        try:
            value = self.user in own_users
        except ObjectDoesNotExist:
            pass
        return value

    def save(self, *args, **kwargs):
        now = datetime.now()
        self.created = now - timedelta(hours=PacificTimeShift.get(now))
        super(AuditLog, self).save(*args, **kwargs)

    @property
    def diff_field(self):
        diff = {}
        if self.old_data != 'null' and self.new_data != 'null':
            try:
                old = json.loads(self.old_data)
            except ValueError:
                old = eval(self.old_data)

            try:
                new = json.loads(self.new_data)
            except ValueError:
                new = eval(self.new_data)

            keys = old.viewkeys() | new.viewkeys()

            for key in keys:
                if self.audit_action == AUDIT_ACTION_ADD and key in new:
                    diff[key] = unicode(' ') + ' => ' + unicode(new.get(key))

                elif self.audit_action == AUDIT_ACTION_UPDATE and key in old and key in new and old[key] != new[key]:
                    diff[key] = unicode(old.get(key)) + ' => ' + unicode(new.get(key))

                elif self.audit_action == AUDIT_ACTION_DELETE:
                    if key in old and key in new and old[key] != new[key]:
                        diff[key] = unicode(old.get(key)) + ' => ' + unicode(new.get(key))

                    elif key in old and not new:
                        diff[key] = unicode(old.get(key)) + ' => ' + unicode(' ')

        return diff

    @property
    def item(self):
        from restapi.audit_logger import AuditLogger
        model = AuditLogger.get_model_by_audit_type(self.audit_type)
        instance = None
        if model is not None:
            qs = model.objects.filter(pk=self.item_id)
            if qs.exists():
                instance = qs.first()
            else:
                try:
                    old_data = json.loads(self.old_data)
                except ValueError:
                    old_data = None

                if old_data:
                    instance = model()
                    for key in old_data:
                        try:
                            setattr(instance, key, old_data[key])
                        except (ValueError, TypeError):
                            pass
        return instance

    @property
    def item_name(self):
        instance = None
        try:
            instance = self.item
        except PermissionDeniedException:
            pass
        return unicode(instance) if instance is not None else None

    class Meta:
        managed = True
        db_table = 'audit_log'
        app_label = 'restapi'
        ordering = ['-audit_log_id']

    def __unicode__(self):
        return self.audit_log_id
