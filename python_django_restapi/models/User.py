# encoding: utf-8

from __future__ import unicode_literals

from django.contrib.auth.hashers import (check_password, make_password, is_password_usable)
from django.utils.crypto import salted_hmac
from django.db import models

from restapi.models import base
from restapi.models.base import BaseModel
from restapi.models.managers import BaseManager
from restapi.models.fields import DateTimeField
from restapi.models.UserPermissionsMixin import UserPermissionsMixin
from restapi.models.TradingDesk import MANAGE_TRADING_DESK_ID, TradingDesk
from restapi.registry import REGISTRY
import restapi.audit_logger as audit
import restapi.http_caching as http_caching

from django.contrib.auth.models import PermissionsMixin, UserManager as DjangoUserManager

AUDIT_TYPE_USER = 1


class UserManager(BaseManager, DjangoUserManager):
    def own(self, queryset=None):
        queryset = super(UserManager, self).own(queryset)
        queryset = queryset.filter(profile__trading_desk__trading_desk_id__in=REGISTRY['user_trading_desk_ids'])
        return queryset


class UserDefaultManager(models.Manager):
    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})


class User(BaseModel, UserPermissionsMixin, PermissionsMixin):
    user_id = models.AutoField(primary_key=True, db_column='id')
    username = models.CharField(max_length=75, blank=False, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.CharField(max_length=75, blank=False)
    is_staff = models.BooleanField(default=1)
    is_active = models.BooleanField(default=1)
    date_joined = DateTimeField(auto_now_add=True, null=True, default=None)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(null=True)

    objects = UserManager()
    objects_raw = UserDefaultManager()
    permission_check = True

    actions = ['filter_by_trading_desk']

    # dummy field for UserSerializer.reset_password_url
    reset_password_url = None

    def is_own(self):
        if self.pk is None:
            return True
        user = REGISTRY.get('user')
        if not user:
            return False
        trading_desk = self.profile.trading_desk.first()
        advertiser = self.profile.advertisers.first()
        if not advertiser and trading_desk:
            user_trading_desk = user.trading_desk.first()
            return user_trading_desk and trading_desk.pk == user_trading_desk.pk
        return user.pk == self.pk

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ('email',)

    def __unicode__(self):
        return self.email

    @property
    def user_in_groups(self):
        return [x.name for x in self.groups.all()]

    @property
    def user_in_trading_desks(self):
        profile = self.profile
        trading_desks = TradingDesk.objects_raw.filter(trading_desk_userprofiles=profile)
        return [x.trading_desk for x in trading_desks]

    @property
    def full_name(self):
        return ('%s %s' % (self.first_name, self.last_name)).strip()

    @property
    def trading_desk(self):
        trading_desks = self.profile.trading_desk
        td = trading_desks.first()
        if td is not None:
            return td.trading_desk
        else:
            return None

    @property
    def trading_desk_id(self):
        trading_desks = self.profile.trading_desk
        td = trading_desks.first()
        if td is not None:
            return td.trading_desk_id
        else:
            return None

    @property
    def trading_desk_key(self):
        trading_desks = self.profile.trading_desk
        td = trading_desks.first()
        if td is not None:
            return td.trading_desk_key
        else:
            return None

    @property
    def is_manage_user(self):
        """Returns True if user is Manage.com user."""
        try:
            return self.profile.trading_desk.filter(pk=MANAGE_TRADING_DESK_ID).exists()
        except base.PermissionDeniedException:
            return False

    def get_short_name(self):
        return self.username

    def get_username(self):
        """Returns the identifying username for this User."""
        return getattr(self, self.USERNAME_FIELD)

    def __str__(self):
        return self.get_username()

    def natural_key(self):
        return (self.get_username(),)

    def is_anonymous(self):
        """
        Always returns False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """

        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=["password"])

        return check_password(raw_password, self.password, setter)

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = make_password(None)

    def has_usable_password(self):
        return is_password_usable(self.password)

    def get_session_auth_hash(self):
        """
        Returns an HMAC of the password field.
        """
        key_salt = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"
        return salted_hmac(key_salt, self.password).hexdigest()

    def get_reset_password_hash(self):
        key_salt = self.trading_desk_key
        data = "%s:%s:%s" % (self.pk, self.password, self.is_active)
        return salted_hmac(key_salt, data).hexdigest()

    def as_dict(self, difference_from=None):
        data = super(User, self).as_dict()
        del data['last_login']
        del data['date_joined']
        data['user_in_groups'] = self.user_in_groups
        data['user_in_trading_desks'] = self.user_in_trading_desks
        return data

    class Meta:
        swappable = 'AUTH_USER_MODEL'
        db_table = 'auth_user'
        app_label = 'restapi'


audit.AuditLogger.register(User, audit_type=AUDIT_TYPE_USER, check_delete='physical_delete')
http_caching.HTTPCaching.register(User)
