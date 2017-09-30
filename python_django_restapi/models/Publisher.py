from django.db import models

from restapi.models.base import BaseModel
from restapi.models.base import BaseReadonlyModelMixin
from restapi.models.choices import PUBLISHER_STATUS_APPROVED
from restapi.models.choices import PUBLISHER_STATUS_CHOICES
from restapi.models.managers import BaseManager


class PublisherManager(BaseManager):
    pass


class Publisher(BaseReadonlyModelMixin, BaseModel):
    publisher_id = models.AutoField(primary_key=True)
    publisher = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=PUBLISHER_STATUS_CHOICES, default=PUBLISHER_STATUS_APPROVED)

    objects = PublisherManager()
    objects_raw = models.Manager()

    def __unicode__(self):
        return self.publisher

    class Meta:
        # managed=False
        db_table = 'publisher'
        app_label = 'restapi'
