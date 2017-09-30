from django.db import models
from restapi.models.base import BaseModel
from restapi.models.managers import BaseManager


class MraidAdTemplateManager(BaseManager):
    pass


class MraidAdTemplate(BaseModel):
    mraid_template_id = models.AutoField(primary_key=True, db_column='mraid_template_id')
    template_name = models.CharField(max_length=255)
    js_tag_version = models.CharField(max_length=32)
    banner_tag_version = models.CharField(max_length=32, blank=True)
    template = models.TextField(blank=True)

    objects = MraidAdTemplateManager()
    objects_raw = models.Manager()
    permission_check = False

    def __unicode__(self):
        return self.template_name

    class Meta:
        managed = True
        db_table = 'mraid_ad_template'
        app_label = 'restapi'
