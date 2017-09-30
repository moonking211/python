from rest_framework.exceptions import ValidationError

from restapi.models.Source import Source
from restapi.models.choices import CLASS_CHOICES
from restapi.testspecs.CreateTestData import CreateTestData
from restapi.views.custom_hint.CustomHintBulk import CustomHintBulk
from restapi.models.CustomHint import CustomHintIds

from mng.test import spec
from mock import Mock


class CustomHintBulkSpec(spec(CustomHintBulk), CreateTestData):
    custom_hint_bulk_service = None
    request = None
    subject = None

    source = None
    source1 = None

    def before_each(self):
        self._create_client()

        self.source = Source(source='name', class_value=CLASS_CHOICES[0][0])
        self.source.save()

        self.source1 = Source(source='name_1', class_value=CLASS_CHOICES[0][0])
        self.source1.save()

        custom_hint_service = Mock()
        request = Mock()
        request.QUERY_PARAMS = {}

        self.request = request
        self.custom_hint_bulk_service = custom_hint_service
        self.subject = CustomHintBulk(custom_hint_service=lambda: custom_hint_service)

    def test__post__custom_hint_bulk_validation_error(self):
        self.request.DATA = {
            'delete': [],
            'save': [
                {'campaign_id': 0,
                 'ad_group_id': 0,
                 'ad_id': 0,
                 'source_id': self.source.pk,
                 'size': '300x250',
                 'placement_type': 'site',
                 'placement_id': 'some_id'
                },
                {'campaign_id': 0,
                 'ad_group_id': 0,
                 'ad_id': 0,
                 'source_id': 0,
                 'size': '300x250',
                 'placement_type': 'Site',
                 'placement_id': 'some_id'
                }
            ]
        }
        self.assertRaises(ValidationError, self.subject.post, self.request)

    def test__post__custom_hint_bulk_upload(self):
        self.request.DATA = {
            'delete': [],
            'save': [
                {'campaign_id': 0,
                 'ad_group_id': 0,
                 'ad_id': 0,
                 'source_id': self.source1.pk,
                 'size': '300x250',
                 'placement_type': 'site',
                 'placement_id': 'some_id',
                 'end_date': '2016-10-04T12:05:00Z'
                },
                {'campaign_id': 0,
                 'ad_group_id': 0,
                 'ad_id': 0,
                 'source_id': self.source.pk,
                 'size': '300x250',
                 'placement_type': 'site',
                 'placement_id': 'some_id_1',
                 'end_date': '2016-11-05T12:05:00Z'
                }
            ]
        }
        response = self.subject.post(self.request)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(CustomHintIds.objects.count() == 2)
