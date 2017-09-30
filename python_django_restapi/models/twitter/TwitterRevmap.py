from django.db import models

from restapi.models.base import BaseModel
from restapi.models.choices import OPT_TYPE_CHOICES
from restapi.models.managers import BaseManager
from restapi.models.Campaign import Campaign
from restapi.models.twitter import TwitterCampaign
from restapi.models.twitter import TwitterLineItem
from restapi.models.fields import DateTimeField


class TwitterRevmapManager(BaseManager):
    pass



class TwitterRevmap(BaseModel):
    revmap_id = models.AutoField(primary_key=True, db_column='id')
    campaign_id = models.OneToOneField(Campaign, db_column='campaign_id', related_name='revmap')
    tw_campaign_id = models.ForeignKey(TwitterCampaign.TwitterCampaign, default=0, db_constraint=False,
                                       db_column='tw_campaign_id')
    tw_line_item_id = models.ForeignKey(TwitterLineItem.TwitterLineItem, default=0, db_constraint=False,
                                        db_column='tw_line_item_id')
    opt_type = models.CharField(max_length=10,
                                blank=True,
                                choices=OPT_TYPE_CHOICES,
                                default=OPT_TYPE_CHOICES[3][0])
    opt_value = models.DecimalField(max_digits=9, decimal_places=4, default=0)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = TwitterRevmapManager()
    objects_raw = models.Manager()

    def __unicode__(self):
        return self.campaign_id

    class Meta:
        managed = True
        db_table = 'tw_revmap'
        app_label = 'restapi'
        unique_together = ('campaign_id', 'tw_campaign_id', 'tw_line_item_id')
