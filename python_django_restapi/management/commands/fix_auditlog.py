import json
from django.core.management.base import BaseCommand
from restapi.audit_logger import AuditLogger
from restapi.models.AuditLog import AUDIT_ACTION_UPDATE
from restapi.models.AuditLog import AuditLog
from restapi.models.AdGroup import AUDIT_TYPE_AD_GROUP
from restapi.models.Revmap import Revmap

AUDIT_TYPE_REVMAP = 11


class Command(BaseCommand):
    help = 'Moves revmap data into the related adgroup logs'

    def handle(self, *args, **options):
        fields = [u'opt_type', u'opt_value', u'rev_type', u'rev_value', u'target_type', u'target_value']
        AuditLogger.models.append((AUDIT_TYPE_REVMAP, Revmap))
        queryset = AuditLog.objects_raw.filter(audit_type=AUDIT_TYPE_REVMAP)

        for auditlog in queryset:
            revmap = auditlog.item
            if revmap is None or revmap.ad_group_id_id==0:
                continue

            old_data = {}
            try:
                old_data = json.loads(auditlog.old_data)
            except:
                pass

            new_data = {}
            try:
                new_data = json.loads(auditlog.new_data)
            except:
                pass

            old_data = {"revmap_%s" % f: v for f,v in old_data.items() if f in fields}
            new_data = {"revmap_%s" % f: v for f,v in new_data.items() if f in fields}

            auditlog.old_data = old_data
            auditlog.new_data = new_data
            auditlog.audit_type = AUDIT_TYPE_AD_GROUP
            auditlog.item_id = revmap.ad_group_id.pk
            auditlog.audit_action = AUDIT_ACTION_UPDATE
            auditlog.save_raw()
