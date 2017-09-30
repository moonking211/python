from django.test import TestCase
from mock import Mock
import pytz
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

from restapi.models.Source import Source
from restapi.models.choices import CLASS_CHOICES
from restapi.models.CustomHint import CustomHintIds
from restapi.serializers.CustomHintSerializer import CustomHintIdsSerializer
from restapi.testspecs.CreateTestData import CreateTestData
from restapi.time_shifting import PacificTimeShift


class DateTimeTest(TestCase, CreateTestData):
    source = None

    def setUp(self):
        self._create_client()

        self.source = Source(source='name', class_value=CLASS_CHOICES[0][0])
        self.source.save()

    def test__serializator__loading_data_into_serializator(self):
        data = {'ad_group_id': 0,
                'ad_id': 0,
                'campaign_id': 0,
                'start_date': '1000-01-01T00:00:00Z',
                'end_date': '2015-06-01T19:50:20Z',
                'frequency_interval': 0,
                'inflator': 0.9,
                'inflator_type': u'relative',
                'max_frequency': 0,
                'placement_id': u'76e5a4ab2878494999f2c7c4e8c1e031',
                'placement_type': u'app',
                'priority': -1,
                'size': u'all',
                'source_id': self.source.pk,
                'tag': ''}

        request = Mock()
        request.QUERY_PARAMS = {}

        timezone.activate(pytz.utc)

        ser = CustomHintIdsSerializer(data=data, context={'request': request})
        self.assertTrue(ser.is_valid())
        self.assertEqual(ser.validated_data['end_date'].year, 2015)
        self.assertEqual(ser.validated_data['end_date'].month, 6)
        self.assertEqual(ser.validated_data['end_date'].day, 1)
        self.assertEqual(ser.validated_data['end_date'].hour, 19)
        self.assertEqual(ser.validated_data['end_date'].minute, 50)
        self.assertEqual(ser.validated_data['end_date'].second, 20)
        self.assertEqual(str(ser.validated_data['end_date'].tzinfo), "tzutc()")

        instance = ser.save()
        self.__check_instance(instance)

        now = datetime.now(pytz.timezone(settings.TIME_ZONE)) - \
              timedelta(hours=PacificTimeShift.get(instance.last_update))
        last_update = instance.last_update + timedelta(hours=PacificTimeShift.get(instance.last_update))

        self.assertEqual(last_update.year, now.year)
        self.assertEqual(last_update.month, now.month)
        self.assertEqual(last_update.day, now.day)
        self.assertEqual(last_update.hour, now.hour)

        self.assertEqual(last_update.minute, now.minute)
        self.assertEqual(last_update.second, now.second)

        instance2 = CustomHintIds.objects.get(pk=instance.pk)
        self.__check_instance(instance2)

        instance2.save()
        self.__check_instance(instance2)

        instance3 = CustomHintIds.objects.get(pk=instance2.pk)
        self.__check_instance(instance3)

    def __check_instance(self, instance):
        self.assertEqual(instance.end_date.year, 2015)
        self.assertEqual(instance.end_date.month, 6)
        self.assertEqual(instance.end_date.day, 1)
        self.assertEqual(instance.end_date.hour, 19)
        self.assertEqual(instance.end_date.minute, 50)
        self.assertEqual(instance.end_date.second, 20)
        self.assertEqual(str(instance.end_date.tzinfo), "tzutc()")
