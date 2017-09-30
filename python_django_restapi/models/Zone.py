from django.db import models

from mng.commons.crypto import encrypt

from restapi.models.App import App
from restapi.models.base import BaseModel
from restapi.models.choices import COST_METHOD_CHOICES, COST_METHOD_BLANK
from restapi.models.choices import ZONE_ORIENTATION_CHOICES, ZONE_ORIENTATION_BOTH
from restapi.models.choices import ZONE_SIZE_CHOICES, ZONE_SIZE_BLANK
from restapi.models.choices import ZONE_STATUS_CHOICES, ZONE_STATUS_LIVE
from restapi.models.choices import ZONE_AD_TYPE_CHOICES, ZONE_AD_TYPE_DISPLAY_VAST_VOXEL
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager


class ZoneManager(BaseManager):
    pass


class Zone(BaseModel):
    zone_id = models.AutoField(primary_key=True)
    app_id = models.ForeignKey(App, db_column='app_id')
    zone = models.CharField(max_length=255, default='')
    orientation = models.CharField(max_length=9, choices=ZONE_ORIENTATION_CHOICES, default=ZONE_ORIENTATION_BOTH)
    status = models.CharField(max_length=7, choices=ZONE_STATUS_CHOICES, default=ZONE_STATUS_LIVE)
    deleted = models.BooleanField(default=False)
    date_added = DateTimeField(auto_now_add=True)
    date_modified = DateTimeField(auto_now=True)
    cost_method = models.CharField(max_length=8, choices=COST_METHOD_CHOICES, default=COST_METHOD_BLANK)
    cpm = models.FloatField(default=0.0)
    revshare = models.FloatField(default=0.0)
    cost_map = models.TextField(default="")
    bid_floor_map = models.TextField(default="")
    custom_priority = models.TextField(default="")
    size = models.CharField(max_length=8, choices=ZONE_SIZE_CHOICES, default=ZONE_SIZE_BLANK)
    callback_url = models.CharField(max_length=255, default='')
    ad_type = models.IntegerField(choices=ZONE_AD_TYPE_CHOICES, default=ZONE_AD_TYPE_DISPLAY_VAST_VOXEL)
    security_key = models.CharField(max_length=100, null=True, default='')
    video_type = models.IntegerField(default=0)
    locked = models.BooleanField(default=False)

    objects = ZoneManager()
    objects_raw = models.Manager()


    class Meta:
        managed = True
        db_table = 'zone'
        app_label = 'restapi'

    def __unicode__(self):
        title = u'{0} - {1} ({2})'.format(self.zone, self.orientation, self.app)
        return title.encode('ascii', 'ignore')

    @property
    def encrypted_key(self):
        return encrypt(self.zone_id)

    @property
    # pylint: disable=invalid-name
    def os(self):
        return self.app_id.os

    @property
    def app(self):
        return self.app_id.app

    @property
    def ad_type_title(self):
        return dict(ZONE_AD_TYPE_CHOICES)[self.ad_type]
