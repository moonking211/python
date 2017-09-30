from django.db import models

from restapi.models.Advertiser import Advertiser


class AdvertiserProfile(models.Model):
    advertiser = models.OneToOneField(Advertiser)
    email = models.EmailField(max_length=254, null=True, blank=True)
    account_manager = models.ForeignKey('AccountManager',
                                        null=True,
                                        blank=True,
                                        db_constraint=False)

    class Meta:
        db_table = 'advertiserprofile'
        app_label = 'restapi'

    def __unicode__(self):
        return self.advertiser.advertiser
