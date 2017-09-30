from restapi.models.AuditLog import AuditLog
from restapi.serializers.AuditLogSerializer import AuditLogSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class AuditLogDetail(BaseDetail):
    # Retrieve, update or delete a audit log instance.
#    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer

    @property
    def queryset(self):
        return AuditLog.objects.all()
