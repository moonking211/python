import datetime

from django.db import models

from restapi.models.base import BaseModel
from restapi.models.managers import BaseManager
from restapi.models.Ad import Ad


class AdPreviewManager(BaseManager):
    pass


class AdPreview(BaseModel):
    id = models.AutoField(primary_key=True)
    source_id = models.IntegerField(default=None, null=False, blank=False)
    placement_id = models.CharField(max_length=128, default=None, null=False, blank=False)
    device_id = models.CharField(max_length=128, default=None, null=False, blank=False)
    ad_id = models.ForeignKey(Ad, db_column='ad_id')
    last_update = models.DateTimeField()

    objects = AdPreviewManager()
    objects_raw = models.Manager()
    permission_check = False

    def __unicode__(self):
        return self.ad_id

    class Meta:
        managed = True
        db_table = 'ad_preview'
        app_label = 'restapi'
