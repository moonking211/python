from django.db import models
from django.conf import settings
from django.contrib.auth.models import Permission

from restapi.models.TradingDesk import TradingDesk
from restapi.models.Advertiser import Advertiser
from restapi.models.Publisher import Publisher
from restapi.models.base import BaseModel
from restapi.models.choices import PUBLISHER_STATUS_APPROVED


class UserProfile(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile')
    placeholder = models.CharField(max_length=1, default='', blank=True, db_column='placeholder')

    trading_desk = models.ManyToManyField(TradingDesk,
                                          blank=True,
                                          db_table='userprofile_trading_desks',
                                          related_name='trading_desk_userprofiles',
                                          db_constraint=False)
    advertisers = models.ManyToManyField(Advertiser,
                                         blank=True,
                                         db_table='userprofile_advertisers',
                                         related_name='advertiser_userprofiles',
                                         db_constraint=False)
    publishers = models.ManyToManyField(Publisher,
                                        blank=True,
                                        db_table='userprofile_publishers',
                                        related_name='publisher_userprofiles',
                                        db_constraint=False)

    class Meta:
        db_table = 'userprofile'

    def __unicode__(self):
        return self.user.username

    def get_colleagues(self):
        users = self.publishers.first().get_affiliated_users()
        # pylint: disable=bad-builtin, deprecated-lambda
        return filter(lambda u: u.email != self.user.email, users)

    def is_ad_manager(self):
        # pylint: disable=no-member
        return Permission.objects.filter(group__user=self.user, codename='am_admin')

    def is_advertiser(self):
        return self.advertisers.first() != None

    def is_publisher(self):
        return self.publishers.first() != None

    def is_approved_publisher(self):
        try:
            if self.publishers.first().status == PUBLISHER_STATUS_APPROVED:
                return True
            else:
                return False
        # pylint: disable=bare-except
        except:
            return False

    def get_roles(self):
        roles = []
        if self.is_ad_manager():
            roles.append('ad_manager')
        if self.is_advertiser():
            roles.append('advertiser')
        if self.is_publisher():
            roles.append('publisher')
        return roles
