from django.db import models
import restapi.audit_logger as audit
import restapi.http_caching as http_caching
from restapi.models.base import BaseModel
from restapi.models.choices import CLASS_CHOICES
from restapi.models.managers import BaseManager

AUDIT_TYPE_SOURCE = 10


class SourceManager(BaseManager):
    pass


class Source(BaseModel):
    source_id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=255, null=False)
    class_value = models.CharField(db_column='class',
                                   max_length=10,
                                   blank=True,
                                   choices=CLASS_CHOICES,
                                   default=CLASS_CHOICES[0][0])

    objects = SourceManager()
    objects_raw = models.Manager()

    def __unicode__(self):
        return self.source

    class Meta:
        managed = True
        db_table = 'source'
        app_label = 'restapi'

audit.AuditLogger.register(Source, audit_type=AUDIT_TYPE_SOURCE, check_delete='physical_delete')
http_caching.HTTPCaching.register(Source)
