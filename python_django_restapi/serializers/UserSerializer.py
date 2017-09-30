from copy import deepcopy
from datetime import datetime
from dateutil.tz import tzutc
from django.contrib.auth.models import Group
from django.db import transaction
import re
from rest_framework import serializers
from restapi.audit_logger import AuditLogger
from restapi.email import send_mail
from restapi.models.TradingDesk import TradingDesk, MANAGE_TRADING_DESK_ID
from restapi.models.User import User
from restapi.models.UserProfile import UserProfile
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.EmailField import EmailField
from restapi.serializers.BaseModelSerializer import BaseModelSerializer

from restapi.registry import REGISTRY
from restapi.serializers.fields.ListField import ListField

TD_ACCOUNT_MANAGER_GROUP = 'Trading Desk Account Manager'

TD_GROUPS = ['Trading Desk Stakeholder',
             'Trading Desk Campaign Supervisor',
             'Trading Desk Campaign Manager',
             TD_ACCOUNT_MANAGER_GROUP]

MANAGE_GROUPS = ['Manage Stakeholder',
                 'Manage Super User',
                 'Manage AdOps Head',
                 'Manage AdOps Supervisor',
                 'Manage AdOps CM',
                 'Manage Account Manager',
                 'Manage TD Account Manager',
                 'Manage Creative Approval']


class UserSerializer(BaseModelSerializer):
    username = EmailField(max_length=75, allow_blank=False)
    first_name = serializers.CharField(max_length=30, allow_blank=True)
    last_name = serializers.CharField(max_length=30, allow_blank=True)
    email = EmailField(max_length=75, allow_blank=False)
    is_active = serializers.BooleanField(required=True)
    trading_desk = serializers.CharField(required=True, allow_blank=False)
    is_manage_user = serializers.BooleanField(read_only=True)
    date_joined = DateTimeField(read_only=True)
    user_in_groups = ListField(required=True)
    groups = serializers.ManyRelatedField(required=False,
                                          child_relation=serializers.PrimaryKeyRelatedField(queryset=Group.objects.all()))
    reset_password_url = serializers.CharField(required=True)

    required_in_schema = ['first_name', 'last_name', 'groups']


    # pylint: disable=old-style-class
    class Meta:
        model = User
        fields = ('user_id',
                  'username',
                  'first_name',
                  'last_name',
                  'full_name',
                  'email',
                  'is_active',
                  'user_in_groups',
                  'groups',
                  'trading_desk',
                  'trading_desk_id',
                  'is_manage_user',
                  'date_joined',
                  'reset_password_url')

    def to_representation(self, instance, **kwargs):
        to_representation_dict = super(UserSerializer, self).to_representation(instance, **kwargs)

        user_in_groups = []
        if 'user_in_groups' in to_representation_dict:
            for group in to_representation_dict['user_in_groups']:
                if group in TD_GROUPS or group in MANAGE_GROUPS:
                    user_in_groups.append(group)
        to_representation_dict['user_in_groups'] = user_in_groups

        if 'groups' in to_representation_dict:
            del to_representation_dict['groups']

        if 'reset_password_url' in to_representation_dict:
            del to_representation_dict['reset_password_url']

        return to_representation_dict

    @transaction.atomic()
    def create(self, request):
        reset_password_url = request.pop('reset_password_url', None)
        if reset_password_url is None:
            raise serializers.ValidationError({'reset_password_url': 'This field is required'})

        if reset_password_url.find('{token}') == -1 or reset_password_url.find('{username}') == -1:
            raise serializers.ValidationError({'reset_password_url': 'This field must contain {token} and {username} placeholders'})

        groups = list(Group.objects.filter(pk__in=[int(x.pk) for x in request.pop('groups', None)]))
        if groups:
            AuditLogger.skip_next_write = True
            user = super(UserSerializer, self).create(request)
            user.date_joined = datetime.now(tzutc())
            user.groups.add(*groups)
        else:
            raise serializers.ValidationError({'groups': 'User should belong to group'})

        UserProfile.objects.create(user=user)
        obj = TradingDesk.objects.filter(trading_desk=self.initial_data.get('trading_desk', None))
        if obj.exists():
            user.profile.trading_desk.add(obj.first())
        else:
            user.save() # save auditlog
            raise serializers.ValidationError({'trading_desk': 'User should belong to trading desk'})

        user.save() # save auditlog

        reset_password_url = re.sub(r'\{token\}', user.get_reset_password_hash(), reset_password_url)
        reset_password_url = re.sub(r'\{username}', user.username, reset_password_url)

        attrs = {'user': user,
                 'reset_password_url': reset_password_url}

        send_mail(mail_to=user.username,
                  template="new_user",
                  attrs=attrs,
                  mail_from="%s <do-not-reply-support@manage.com>" % user.trading_desk)

        return user

    @transaction.atomic()
    def update(self, instance, validated_data):
        data = deepcopy(validated_data)
        groups = data.pop('groups', [])

        AuditLogger.skip_next_write = True
        super(UserSerializer, self).update(instance, data)

        new_user_in_groups = [x.name for x in groups]
        old_user_in_groups = [x.name for x in instance.groups.all()]

        new_groups = list(Group.objects.filter(
            name__in=[x for x in [x for x in new_user_in_groups if x not in old_user_in_groups]]))
        old_groups = list(Group.objects.filter(
            name__in=[x for x in [x for x in old_user_in_groups if x not in new_user_in_groups]]))

        if old_groups:
            [x.user_set.remove(instance) for x in old_groups if x.name in MANAGE_GROUPS or x.name in TD_GROUPS]

        if new_groups:
            instance.groups.add(*new_groups)

        instance.save() # save auditlog
        return instance

    def is_valid(self, *args, **kwargs):
        valid = super(UserSerializer, self).is_valid(*args, **kwargs)
        instance = self.instance

        # username
        username = self.validated_data.get('username')
        if re.match(r'[^a-zA-Z0-9_\@\+\.\-]', username):
            raise serializers.ValidationError({'username': 'Username may contains alphanumeric, _, @, +, . and - characters.'})

        user = REGISTRY['user']
        user_groups = [g.name for g in user.groups.all()]
        user_in_groups = []
        groups = self.validated_data.get('groups', None)
        if groups:
            user_in_groups = list([x.name for x in Group.objects.filter(pk__in=[int(x.pk) for x in groups])])

        if instance:
            instance_groups = [g.name for g in instance.groups.all()]
            instance_monarch_groups = [g for g in instance_groups if str(g) in MANAGE_GROUPS + TD_GROUPS]

            errors = {}
            for field in ['first_name', 'last_name']:
                if not self.validated_data.get(field, None) and getattr(self.instance, field):
                    errors[field] = 'This field is required'

            if instance_monarch_groups and not self.validated_data.get('groups', None):
                errors['user_in_groups'] = 'This field is required'

            if errors:
                raise serializers.ValidationError(errors)


        if TD_ACCOUNT_MANAGER_GROUP in user_groups:
            for group in user_in_groups:
                if group not in TD_GROUPS:
                    raise serializers.ValidationError('Available groups:%s' % TD_GROUPS.join(','))

        obj = TradingDesk.objects.filter(trading_desk=self.initial_data.get('trading_desk', None))
        if obj.exists():
            obj = obj.first()
        else:
            raise serializers.ValidationError({'trading_desk': 'Invalid value'})

        group_list = TD_GROUPS[:]
        if obj.pk == MANAGE_TRADING_DESK_ID:
            group_list += MANAGE_GROUPS

        for group in user_in_groups:
            if group not in group_list:
                raise serializers.ValidationError('Available groups:%s' % ','.join(group_list))

        return valid
