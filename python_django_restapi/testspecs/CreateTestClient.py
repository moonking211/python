from django.contrib.auth.models import Permission, Group, ContentType
from django.db import connection
from django.test import Client

from restapi.registry import REGISTRY
from restapi.models.UserProfile import UserProfile
from restapi.models.TradingDesk import TradingDesk
from restapi.models.User import User


class CreateTestClient(object):
    def __init__(self):
        self.logged_in_client = None
        self.user = None

    def _create_client(self):
        # create user and login
        username = 'user@mng.com'
        password = 'password1'
        hash_password = 'pbkdf2_sha256$12000$qE1LdpvZySML$ld8xNXbMy/Ilc4E8ERw3ab3IxgLbdleT+scvTLNAqtw='

        cursor = connection.cursor()
        cursor.execute('INSERT INTO auth_user SET password=%s, is_superuser=%s, username=%s,'
                       ' email=%s, is_active=%s, is_staff=%s, first_name=%s, last_name=%s',
                       [hash_password, 1, username, username, 1, 1, 'test', 'test'])
        cursor.close()

        user = User.objects.get(username=username)

        REGISTRY['user'] = user

        UserProfile.objects.create(user=user)
        user.profile.trading_desk.add(TradingDesk.objects.create(trading_desk='trading_desk'))

        group = Group(name='Ad Manager Admin')
        group.save()

        user.groups.add(group)

        content_type = ContentType(name='ad manager', app_label='dashboard', model='admanager')
        content_type.save()

        permission = Permission(name='Ad Manager Admin', content_type=content_type, codename='am_admin')
        permission.save()

        group.permissions.add(permission)

        # pylint: disable=no-member
        self.user = user

        client = Client()
        client.login(username=user.username, password=password)
        self.logged_in_client = client
        return user
