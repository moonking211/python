from django.test import TestCase
import mock
from restapi.serializers.AdGroupSerializer import AdGroupSerializer
from .base import SerializerValidationTextMixin


class AdGroupSerializerSpecs(TestCase, SerializerValidationTextMixin):
    serializer = AdGroupSerializer

    CALL_METHODS = ('_is_valid_frequency_map_375x50_is_not_supported',
                    '_is_valid_no_distributions',
                    '_is_valid_rev_value_negative',
                    '_is_valid_insecure_url',
                    '_is_valid_destination_url',
                    '_is_valid_different_segments',
                    '_is_valid_targeting',
                    '_is_valid_flightings',
                    '_is_valid_base',
                    '_is_valid_inflator')

    def setUp(self):
        pass

    def test__is_valid_frequency_map_375x50_is_not_supported__375x50_is_not_supported_now(self):
        self.set_callee('_is_valid_frequency_map_375x50_is_not_supported')

        data = {'frequency_map': '{"480x240":"1"}'}
        self.assertEqual(self.call(data), {})

        data['frequency_map'] = '{"375x50":"1"}'
        self.assertEqual(self.call(data), {'frequency_map': '375x50 size is currently unsupported'})

    def test__is_valid_no_distributions__no_distributions(self):
        self.set_callee('_is_valid_no_distributions')

        data = {}
        self.assertEqual(self.call(data), {})

        data['distribution_app_sha1_android_id'] = False
        data['distribution_app_ifa'] = True
        data['distribution_web'] = False
        self.assertEqual(self.call(data), {})

        data['distribution_app_ifa'] = False
        self.assertEqual(self.call(data), {'distributions': 'No distributions'})

    def test__is_valid_rev_value_negative__negative_rev_value(self):
        self.set_callee('_is_valid_rev_value_negative')

        data = {'daily_budget_value': 1,
                'daily_cost_cap': 1,
                'daily_loss_cap': 1,
                'flight_budget_value': 1,
                'total_cost_cap': 1,
                'total_loss_cap': 1}
        self.assertEqual(self.call(data), {})
   
        data['revmap_rev_value'] = 10
        self.assertEqual(self.call(data), {})

        data['revmap_rev_value'] = -10
        self.assertEqual(self.call(data), {'revmap_rev_value': 'Rev value could not be negative'})

    def test__is_valid_insecure_url_redirect__insecure_url(self):
        self.set_callee('_is_valid_insecure_url')

        data = {'redirect_url': 'https://monarch.manage.com',
                'ignore_fatigue_segment': False,
                'ignore_suppression_segment': False}
        self.assertEqual(self.call(data), {})

        data['ignore_fatigue_segment'] = True
        data['redirect_url'] = 'http://monarch.manage.com'
        self.assertEqual(self.call(data), {})

        data['ignore_fatigue_segment'] = False
        data['ignore_suppression_segment'] = False
        self.assertEqual(self.call(data), {'redirect_url': 'insecure URL, use https://'})

    def test__is_valid_insecure_url_impression__insecure_url(self):
        self.set_callee('_is_valid_insecure_url')

        data = {'viewthrough_url': None}
        self.assertEqual(self.call(data), {})

        data['viewthrough_url'] = 'https://www.manage.com'
        self.assertEqual(self.call(data), {})

        data['viewthrough_url'] = 'http://www.manage.com'
        self.assertEqual(self.call(data), {'impression url': 'insecure URL, use https://'})

    def test__is_valid_different_segments__different_segments(self):
        self.set_callee('_is_valid_different_segments')

        data = {'ignore_fatigue_segment': False,
                'ignore_suppression_segment': False}
        self.assertEqual(self.call(data), {})

        data['ignore_fatigue_segment'] = True
        data['ignore_suppression_segment'] = True
        self.assertEqual(self.call(data), {})

        data['ignore_fatigue_segment'] = True
        data['ignore_suppression_segment'] = False
        errors = {'ignore_fatigue_segment': 'ignore_fatigue_segment should be the same as ignore_suppression_segment',
                  'ignore_suppression_segment': 'ignore_fatigue_segment should be the same as ignore_suppression_segment'}
        self.assertEqual(self.call(data), errors)

    def test__is_valid_destination_url__destination_url(self):
        self.set_callee('_is_valid_destination_url')
        data = {}
        self.assertEqual(self.call(data), {})

        data['destination_url'] = 'http://monarch.manage.com'
        self.assertEqual(self.call(data), {})

        data['destination_url'] = 'com'
        self.assertEqual(self.call(data), {'destination_url': 'Must be at least 10 characters long'})

    def test__is_valid_targeting__targeting(self):
        self.set_callee('_is_valid_targeting')

        campaign = mock.Mock()
        campaign.targeting = '{}'
        campaign.app_install = False

        data = {'campaign_id': campaign,
                'targeting': '{"country":"US", "os":"iOS", "model":"iPhone"}'}
        self.assertEqual(self.call(data), {})

        data = {'campaign_id': campaign,
                'targeting': '{}'}
        self.assertEqual(self.call(data), {'country': 'You must set County',
                                           'os': "OS must be defined in its or Parent's entity targeting"})

        campaign.targeting = '{"country":"US", "os":"iOS"}'
        self.assertEqual(self.call(data), {'model': 'You must set Model of your device'})

        campaign.targeting = '{"country":"US", "os":"iOS", "model":"iPhone"}'
        self.assertEqual(self.call(data), {})

        data['distribution_app_sha1_android_id'] = True
        self.assertEqual(self.call(data), {'distribution_app_sha1_android_id': 'Cant be selected if os = iOS'})
        data['distribution_app_sha1_android_id'] = False

        data['distribution_app_ifa'] = True
        campaign.targeting = '{"country":"US", "os":"Android", "model":"Android"}'
        self.assertEqual(self.call(data), {'distribution_app_ifa': 'Cant be selected if os = Android'})
        campaign.targeting = '{"country":"US", "os":"Kindle", "model":"Kindle"}'
        self.assertEqual(self.call(data), {'distribution_app_ifa': 'Cant be selected if os = Kindle'})
        data['distribution_app_ifa'] = False

        campaign.app_install = True
        campaign.targeting = '{"country":"US", "os":"iOS", "model":"iPhone"}'
        data['destination_url'] = 'https://itunes.apple.com'
        self.assertEqual(self.call(data), {})
        data['destination_url'] = 'http://monarch.manage.com'
        self.assertEqual(self.call(data), {'destination_url': 'Destination URL must start w/: https://itunes.apple.com'})

        campaign.targeting = '{"country":"US", "os":"Android", "model":"Android"}'
        data['destination_url'] = 'https://play.google.com'
        self.assertEqual(self.call(data), {})
        data['destination_url'] = 'http://monarch.manage.com'
        self.assertEqual(self.call(data), {'destination_url': 'Destination URL must start w/: https://play.google.com'})

    @mock.patch.object(serializer, '_is_valid_frequency_map_375x50_is_not_supported')
    @mock.patch.object(serializer, '_is_valid_no_distributions')
    @mock.patch.object(serializer, '_is_valid_rev_value_negative')
    @mock.patch.object(serializer, '_is_valid_insecure_url')
    @mock.patch.object(serializer, '_is_valid_destination_url')
    @mock.patch.object(serializer, '_is_valid_different_segments')
    @mock.patch.object(serializer, '_is_valid_targeting')
    @mock.patch.object(serializer, '_is_valid_flightings')
    @mock.patch.object(serializer, '_is_valid_base')
    @mock.patch.object(serializer, '_is_valid_inflator')
    @mock.patch.object(serializer, '_get_status')
    @mock.patch.object(serializer, '_get_campaign_id')
    def test__is_valid__was_called(self,
                                   _is_valid_frequency_map_375x50_is_not_supported,
                                   _is_valid_no_distributions,
                                   _is_valid_rev_value_negative,
                                   _is_valid_insecure_url,
                                   _is_valid_destination_url,
                                   _is_valid_different_segments,
                                   _is_valid_targeting,
                                   _is_valid_flightings,
                                   _is_valid_base,
                                   _is_valid_inflator,
                                   _get_status,
                                   _get_campaign_id):

        test_serializer_method_calls = self.serializer(data={}, context={'request': ''}, instance={})
        test_serializer_method_calls.is_valid()
        for method in self.CALL_METHODS:
            self.assertTrue(getattr(self.serializer, method).called)
