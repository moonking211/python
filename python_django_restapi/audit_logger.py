from copy import deepcopy
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete

from restapi.models.AuditLog import AUDIT_ACTION_ADD
from restapi.models.AuditLog import AUDIT_ACTION_UPDATE
from restapi.models.AuditLog import AUDIT_ACTION_DELETE
from restapi.models.AuditLog import AuditLog
from restapi.models.base import dict_as_json
from restapi.registry import REGISTRY


class AuditLogger(object):
    new_data = None
    old_data = None
    physical_delete = False
    models = []
    skip_next_write = False

    def __init__(self, audit_type, check_delete='status'):
        self.audit_type = audit_type
        if check_delete == 'deleted':
            self.check_delete = self.check_delete_by_deleted
        elif check_delete == 'status':
            self.check_delete = self.check_delete_by_status
        elif check_delete == 'disabled':
            self.check_delete = self.check_delete_disabled
        elif check_delete == 'physical_delete':
            self.check_delete = self.check_physical_delete
        self.old_data = {}
        self.new_data = {}

    @classmethod
    def register(cls, model_cls, *args, **kwargs):
        audit_type = kwargs.get('audit_type', None)
        cls.models.append((audit_type, model_cls))
        model_cls.audit_logger = AuditLogger(*args, **kwargs)
        pre_save.connect(cls.save_old_data, sender=model_cls)
        post_save.connect(cls.audit_log, sender=model_cls)
        pre_delete.connect(cls.pre_delete, sender=model_cls)
        post_delete.connect(cls.audit_log, sender=model_cls)

    @classmethod
    def get_model_by_audit_type(cls, audit_type):
        for model_audit_type, model in cls.models:
            if model_audit_type == audit_type:
                return model
        return None

    @staticmethod
    # pylint: disable=unused-argument
    def save_old_data(sender, instance, **kwargs):
        # pylint: disable=protected-access
        instance.audit_logger.__save_old_data(instance)

    @staticmethod
    # pylint: disable=unused-argument
    def pre_delete(sender, instance, **kwargs):
        instance.audit_logger.physical_delete = True
        # pylint: disable=protected-access
        instance.audit_logger.__save_old_data(instance)

    @staticmethod
    def __save_old_data(instance):
        if hasattr(instance, 'audit_logger_skip_read'):
            return
        instance.audit_logger.old_data = {}
        if instance.pk:
            try:
                instance.audit_logger.old_data = instance.__class__.objects.get(pk=instance.pk).as_dict()
            except instance.DoesNotExist:
                return

    @staticmethod
    # pylint: disable=bad-staticmethod-argument,unused-argument
    def check_physical_delete(self):
        return self.physical_delete

    @staticmethod
    # pylint: disable=unused-argument
    def audit_log(sender, instance, **kwargs):
        if AuditLogger.skip_next_write:
            AuditLogger.skip_next_write = False
            instance.audit_logger_skip_read = True
            return

        if hasattr(instance, 'audit_logger_skip_read'):
            delattr(instance, "audit_logger_skip_read")

        self = instance.audit_logger
        instance.fix_datetimes()

        if settings.SYSTEM_USER is True:
            User = get_user_model()
            try:
                user = User.objects.get(pk=settings.SYSTEM_USER_ID)
            except User.DoesNotExist:
                return
        elif 'user' in REGISTRY and REGISTRY['user'] and not REGISTRY['user'].is_anonymous() and REGISTRY['user'].is_authenticated():
            user = REGISTRY['user']
        else:
            return

        audit_type = self.audit_type
        audit_action = self.get_action()
        item_id = instance.pk

        old_data = deepcopy(self.old_data) if instance.pk else {}
        if not self.physical_delete:
            real_instance = instance.__class__.objects_raw.get(pk=instance.pk)
            new_data = real_instance.as_dict()
        else:
            new_data = {}

        self._remove_data_intersection(old_data, new_data)

        # remove auto-generated fields
        for field in instance._meta.fields:
            if (hasattr(field, 'auto_now') and field.auto_now) or (hasattr(field, 'auto_now_add') and field.auto_now_add):
                if field.name in old_data:
                    del old_data[field.name]
                if field.name in new_data:
                    del new_data[field.name]

        if not settings.DISABLE_AUDIT_LOG and (old_data or new_data):
            obj = AuditLog(user=user,
                           audit_type=audit_type,
                           audit_action=audit_action,
                           item_id=item_id,
                           old_data=dict_as_json(old_data),
                           new_data=dict_as_json(new_data))
            obj.save_raw()
            instance.audit_logger.physical_delete = False

    def _remove_data_intersection(self, dict1, dict2):
        keys = set(dict1.keys() + dict2.keys())
        for k in keys:
            if k in dict1 and k in dict2 and dict1[k] == dict2[k]:
                del dict1[k]
                del dict2[k]

    def get_action(self):
        audit_action = AUDIT_ACTION_ADD
        if bool(self.old_data):
            audit_action = AUDIT_ACTION_UPDATE
        if self.check_delete(self):
            audit_action = AUDIT_ACTION_DELETE
        return audit_action

    @staticmethod
    # pylint: disable=bad-staticmethod-argument
    def check_delete_by_deleted(self):
        return bool(self.old_data) and not self.old_data['deleted'] and self.new_data['deleted']

    @staticmethod
    # pylint: disable=bad-staticmethod-argument
    def check_delete_by_status(self):
        if not bool(self.old_data):
            return False
        if self.old_data['status'] == 'deleted':
            return False
        if not self.new_data['status'] == 'deleted':
            return False
        return True

    @staticmethod
    # pylint: disable=bad-staticmethod-argument,unused-argument
    def check_delete_disabled(self):
        return False
