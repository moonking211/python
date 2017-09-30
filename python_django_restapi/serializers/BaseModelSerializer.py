# encoding :utf-8
"""This module defines BaseModelSerializer class."""

from __future__ import unicode_literals

from collections import OrderedDict
import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db import models
from django.db.models.fields import FieldDoesNotExist

from rest_framework import serializers
from rest_framework.relations import ManyRelatedField

from restapi.registry import REGISTRY
from restapi.models.base import PermissionDeniedException
from restapi.models.fields import JSONField


class BaseModelSerializer(serializers.ModelSerializer):
    """
    `BaseModelSerializer` is a regular `Serializer`, except that it enables you specify fields you want to have in the
     output results. The '$select' argument in the query string specifies resulting fields.
    """

    required_in_schema = []
    permissions_extra_fields = []

    def get_fields(self):
        fields = OrderedDict()
        all_fields = super(BaseModelSerializer, self).get_fields()
        select_field_names = self._get_select_field_names()
        if select_field_names is not None:
            for name in select_field_names:
                fields[name] = all_fields[name]
            return fields
        return all_fields

    def _get_select_field_names(self):
        if 'request' in self.context and '$select' in self.context['request'].QUERY_PARAMS:
            names = [unicode(name.strip()) for name in self.context['request'].QUERY_PARAMS['$select'].split(',')]
            return names
        return None

    @property
    def model(self):
        return self.Meta.model

    @property
    def model_name(self):
        return self.Meta.model._meta.model_name

    def is_valid(self, *args, **kwargs):
        if not self.model.permission_check:
            return super(BaseModelSerializer, self).is_valid(*args, **kwargs)

        initial_data = self.initial_data
        instance = self.instance
        if instance:
            permitted_fields = self.__permitted_instance_fields(instance, 'update')

        else:
            instance = self.model()
            for attr, value in initial_data.items():
                if attr not in self.fields:
                    continue
                field = self.fields[attr]
                if field.read_only:
                    continue
                if isinstance(field, serializers.PrimaryKeyRelatedField):
                    try:
                        value = field.get_queryset().model.objects.get(pk=value)
                    except ObjectDoesNotExist:
                        value = None

                # this is s big spike need to rework
                if isinstance(field, ManyRelatedField):
                    continue

                if isinstance(field, serializers.IntegerField):
                    if value is not None and value != '':
                        value = int(value)
                    else:
                        value = None

                try:
                    setattr(instance, attr, value)
                except Exception:
                    logging.exception('Unexpected exception')

            instance.autopopulate_by_ownership()
            permitted_fields = self.__permitted_instance_fields(instance, 'create')

        for name, field in self.fields.items():
            if self.fields[name].read_only:
                continue
            if name not in permitted_fields:
                if isinstance(field, serializers.PrimaryKeyRelatedField):
                    initial_data[name] = getattr(instance, name).pk
                elif isinstance(field, ManyRelatedField):
                    continue
                else:
                    initial_data[name] = getattr(instance, name)
        return super(BaseModelSerializer, self).is_valid(*args, **kwargs)

    def update(self, instance, validated_data):
        """Updates given instance with a given validated_data.

        :param instance: a model instance to update.
        :param validated_data: a dict with validated data to update instance.
        :return: modified instance.
        """
        modified_attributes = set()

        if not self.model.permission_check:
            for attr, value in validated_data.items():
                if not self.fields[attr].read_only:
                    setattr(instance, attr, value)
                    modified_attributes.add(attr)
            if instance.pk and modified_attributes:
                instance.save(update_fields=modified_attributes)
            else:
                instance.save()
            return instance

        permitted_fields = self.__permitted_instance_fields(instance, 'update')
        for attr, value in validated_data.items():
            try:
                old_value = getattr(instance, attr)
            except ObjectDoesNotExist:
                old_value = None
            try:
                field = self.model._meta.get_field_by_name(attr)[0]
                if isinstance(field, JSONField):
                    old_value = json.dumps(old_value)
            except FieldDoesNotExist:
                pass
            if not self.fields[attr].read_only and value != old_value:
                if attr not in permitted_fields:
                    raise PermissionDeniedException("Access forbidden :%s" % attr)
                try:
                    setattr(instance, attr, value)
                    if field and not isinstance(field, models.ManyToManyField):
                        modified_attributes.add(attr)
                except AttributeError:  # try to update property
                    logging.exception('Unexpected exception')
        try:
            update_fields = set([field.name for field in self.model._meta.fields]) & modified_attributes
            if instance.pk and update_fields:
                instance.save(update_fields=update_fields)
            else:
                instance.save()
        except IntegrityError as error:
            raise serializers.ValidationError("DBIntegrityError:%s" % error)

        return instance

    def create(self, validated_data):
        # pylint: disable=no-member
        instance = self.Meta.model(**validated_data)
        try:
            instance.save()
        except IntegrityError as error:
            raise serializers.ValidationError("DBIntegrityError:%s" % error)
        return instance

    def to_representation(self, instance, **kwargs):
        data = super(BaseModelSerializer, self).to_representation(instance, **kwargs)
        if self.model.permission_check:
            result = OrderedDict()
            real_instance = instance

            if isinstance(real_instance, OrderedDict):  # instance - OrderedDict in case of CSV import
                primary_key = self.model._meta.pk.name
                real_instance = self.model.objects.get(pk=instance[primary_key])

            permitted_fields = self.__permitted_instance_fields(real_instance, 'read')

            for key, value in data.items():
                if key in permitted_fields:
                    result[key] = value
            data = result
        return data

    def __permitted_instance_fields(self, instance, action):
        user = REGISTRY.get('user', None)
        return user.get_permitted_instance_fields(instance=instance, action=action, fields=self.fields.keys())
