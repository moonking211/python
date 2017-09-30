from django.db import models
from django.utils.http import int_to_base36, base36_to_int
from restapi.models.choices import STATUS_CHOICES, STATUS_PAUSED, STATUS_ENABLED
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager


class TwitterUserManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(TwitterUserManager, self).own(queryset)
        return queryset


class TwitterUser(BaseModel):
    tw_twitter_user_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=255)
    oauth_token = models.CharField(max_length=255)
    oauth_secret = models.CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = TwitterUserManager()
    objects_raw = models.Manager()
    # permission_check = True

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tw_twitter_user'
        app_label = 'restapi'
