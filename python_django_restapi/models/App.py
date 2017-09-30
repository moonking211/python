from django.db import models

from restapi.models.Publisher import Publisher
from restapi.models.base import BaseModel
from restapi.models.base import BaseReadonlyModelMixin
from restapi.models.fields import DateTimeField
from restapi.models.choices import OS_CHOICES
from restapi.models.choices import COST_METHOD_CHOICES, COST_METHOD_REVSHARE
from restapi.models.managers import BaseManager


class AppManager(BaseManager):
    pass


class App(BaseReadonlyModelMixin, BaseModel):
    app_id = models.AutoField(primary_key=True)
    publisher_id = models.ForeignKey(Publisher, db_column='publisher_id')
    app = models.CharField(max_length=255)
    os = models.CharField(max_length=7, choices=OS_CHOICES) # pylint: disable=invalid-name
    app_url = models.CharField(max_length=255)
    category1 = models.CharField(max_length=255)
    category2 = models.CharField(max_length=255)
    bcat = models.TextField()
    badv = models.TextField()
    battr = models.CharField(max_length=255)
    deleted = models.BooleanField(default=False)
    date_added = DateTimeField()
    date_modified = DateTimeField()
    cost_method = models.CharField(max_length=8,
                                   default=COST_METHOD_REVSHARE,
                                   choices=COST_METHOD_CHOICES)
    cpm = models.FloatField(default=0.0)
    revshare = models.FloatField(default=0.6)
    cost_map = models.TextField()
    bid_floor_map = models.TextField()
    bg_frames = models.TextField()
    video_enabled = models.BooleanField(default=True)
    tier1_approved = models.BooleanField(default=False)

    objects = AppManager()
    objects_raw = models.Manager()

    class Meta:
        managed = True
        db_table = 'app'
        app_label = 'restapi'

    def __unicode__(self):
        return self.os + " - " + self.app
