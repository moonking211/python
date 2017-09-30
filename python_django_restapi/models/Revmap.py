from django.db import models

from restapi.models.base import BaseModel
from restapi.models.choices import OPT_TYPE_CHOICES
from restapi.models.managers import BaseManager
from restapi.models.AdGroup import AdGroup
from restapi.models.fields import DateTimeField
import restapi.audit_logger as audit
import restapi.http_caching as http_caching


class RevmapManager(BaseManager):
    pass


class Revmap(BaseModel):
    revmap_id = models.AutoField(primary_key=True, db_column='id')
    ad_group_id = models.OneToOneField(AdGroup, db_column='ad_group_id', related_name='revmap')
    ad_group = models.CharField(max_length=255)
    campaign_id = models.IntegerField(blank=False, null=False, default=None)
    campaign = models.CharField(max_length=255)
    opt_type = models.CharField(max_length=10,
                                blank=True,
                                choices=OPT_TYPE_CHOICES,
                                default=OPT_TYPE_CHOICES[3][0])
    opt_value = models.DecimalField(max_digits=9, decimal_places=4, default=0)
    rev_type = models.CharField(max_length=10,
                                blank=True,
                                choices=OPT_TYPE_CHOICES,
                                default=OPT_TYPE_CHOICES[3][0])
    rev_value = models.DecimalField(max_digits=9, decimal_places=4, default=0)
    target_type = models.CharField(max_length=10,
                                   blank=True,
                                   choices=OPT_TYPE_CHOICES,
                                   default=OPT_TYPE_CHOICES[3][0])
    target_value = models.DecimalField(max_digits=9, decimal_places=4, default=0)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = RevmapManager()
    objects_raw = models.Manager()

    def __unicode__(self):
        return self.ad_group

    def make_copy(self):
        rejected_fields = lambda x: x.__class__ is models.AutoField or x.name == 'pk'
        values = [
            (f.name, getattr(self, f.name)) for f in self._meta.fields if not rejected_fields(f)
        ]
        initials = dict([(k, v) for k, v in values if v is not None])
        # pylint: disable=invalid-name
        m = self.__class__(**initials)
        # pylint: disable=invalid-name
        m.pk = None
        return m

    class Meta:
        managed = True
        db_table = 'revmap'
        app_label = 'restapi'
