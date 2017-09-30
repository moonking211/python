from django.db import models
from restapi.models.AuditLog import AuditLog
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.DateTimeField import DateTimeField


class AuditLogSerializer(BaseModelSerializer):
    diff_field = models.TextField(blank=True)
    created = DateTimeField(read_only=True)

     # pylint: disable=unused-argument
    def create(self, *args, **kwargs):
        raise Exception('Can notcreate anything in', self.__class__.__name__)

    # pylint: disable=unused-argument
    def update(self, *args, **kwargs):
        raise Exception('Can not update anything in', self.__class__.__name__)

    # pylint: disable=old-style-class
    class Meta:
        model = AuditLog
        fields = ('audit_log_id',
                  'user',
                  'audit_type',
                  'audit_action',
                  'item_id',
                  'item_name',
                  'old_data',
                  'new_data',
                  'created',
                  'diff_field')
