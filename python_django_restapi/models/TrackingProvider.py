from django.db import models
from restapi.models.base import BaseModel
from restapi.models.managers import BaseManager


class TrackingProviderManager(BaseManager):
    pass


class TrackingProvider(BaseModel):
    tracking_provider_id = models.AutoField(primary_key=True)
    tracking_provider = models.CharField(max_length=255)

    objects = TrackingProviderManager()
    objects_raw = models.Manager()

    def __unicode__(self):
        return self.source

    class Meta:
        managed = True
        db_table = 'tracking_provider'
        app_label = 'restapi'
