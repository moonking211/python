from django.test import TestCase
import mock
from restapi.serializers.CampaignSerializer import CampaignSerializer
from .base import SerializerValidationTextMixin


class CampaignSerializerSpecs(TestCase, SerializerValidationTextMixin):
    serializer = CampaignSerializer

    CALL_METHODS = ('_is_valid_frequency_map',
                    '_is_valid_no_distributions',
                    '_is_valid_flight_budget_data',
                    '_is_valid_attribution_window',
                    '_is_valid_domain',
                    '_is_valid_app_install',
                    '_is_valid_urls',
                    '_is_valid_priority',
                    '_is_valid_genre',
                    '_is_valid_app_classifications',
                    '_is_valid_base',
                    '_is_valid_inflator')

    def setUp(self):
        pass

    def test__is_valid_no_distributions__no_distributions(self):
        self.set_callee('_is_valid_no_distributions')

        data = {}
        self.assertEqual(self.call(data), {'distributions': 'No distributions'})

        data['distribution_app_sha1_android_id'] = False
        data['distribution_app_ifa'] = True
        data['distribution_web'] = False
        self.assertEqual(self.call(data), {})

        data['distribution_app_ifa'] = False
        self.assertEqual(self.call(data), {'distributions': 'No distributions'})

    def test__is_valid_priority__for_campaigns(self):
        self.set_callee('_is_valid_priority')

        data = {'priority': 1}
        self.assertEqual(self.call(data), {})

        data['priority'] = 101
        self.assertEqual(self.call(data), {'priority': 'Priority can not be less than 0 and more than 100'})

        data['priority'] = -1
        self.assertEqual(self.call(data), {'priority': 'Priority can not be less than 0 and more than 100'})

    def test__is_valid_domain__for_campaigns(self):
        self.set_callee('_is_valid_domain')

        data = {'domain': 'test.com'}
        self.assertEqual(self.call(data), {})

        data['domain'] = 'http://test.com'
        self.assertEqual(self.call(data), {'domain': 'should not contain http:// or https:// and must be valid url'})

        data['domain'] = 'https://test.com'
        self.assertEqual(self.call(data), {'domain': 'should not contain http:// or https:// and must be valid url'})

        data['domain'] = 'te//st.com'
        self.assertEqual(self.call(data), {'domain': 'should not contain http:// or https:// and must be valid url'})

    def test__is_valid_frequency_map__for_campaigns(self):
        self.set_callee('_is_valid_frequency_map')

        data = {'frequency_map': '{"480x240":"1"}'}
        self.assertEqual(self.call(data), {})

        data['frequency_map'] = '{"375x50":"1"}'
        self.assertEqual(self.call(data), {'frequency_map': '375x50 size is currently unsupported'})

    def test__is_valid_flight_budget_data__for_campaigns(self):
        self.set_callee('_is_valid_flight_budget_data')

        data = {'flight_start_date': '2016-06-28T01:00:00Z',
                'flight_end_date': '2016-06-29T00:59:00Z',
                'daily_budget_value': 1,
                'daily_cost_cap': 1,
                'daily_loss_cap': 1,
                'flight_budget_type': 'impression',
                'flight_budget_value': 1,
                'total_cost_cap': 1,
                'total_loss_cap': 1}
        self.assertEqual(self.call(data), {})

        data['flight_start_date'] = '2016-06-29T01:00:00Z'
        data['flight_end_date'] = '2016-06-28T00:59:00Z'
        self.assertEqual(self.call(data),
                         {'flight start/end dates': 'flight start date need to be before flight end date'})

        data['daily_budget_value'] = '3.00'
        data['flight_budget_value'] = '2.00'
        data['flight_end_date'] = '2016-07-28T00:59:00Z'
        data['flight_budget_type'] = ''
        self.assertEqual(self.call(data), {'flight budget type': 'You must set Flight Budget Type'})
        data['flight_budget_type'] = 'impression'

        data['flight_start_date'] = ''
        self.assertEqual(self.call(data), {'flight start date': 'You must set Flight Start Date'})
        data['flight_start_date'] = '2016-06-28T01:00:00Z'

        data['flight_budget_value'] = ''
        self.assertEqual(self.call(data), {})

    def test__is_valid_app_install__for_campaigns(self):
        self.set_callee('_is_valid_app_install')

        data = {'targeting': '{"os":"iOS"}', 'app_install': True, 'destination_url': 'https://itunes.apple.com'}
        self.assertEqual(self.call(data), {})

        data['destination_url'] = 'SomeOtherUrl.com'
        self.assertEqual(self.call(data),
                         {'destination_url': 'Destination URL must start w/: https://itunes.apple.com'})

        data['targeting'] = '{"os":"Android"}'
        data['destination_url'] = 'https://play.google.com'
        self.assertEqual(self.call(data), {})

        data['destination_url'] = 'SomeOtherUrl.com'
        self.assertEqual(self.call(data), {'destination_url': 'Destination URL must start w/: https://play.google.com'})

    def test__is_valid_urls__for_campaigns(self):
        self.set_callee('_is_valid_urls')

        data = {'redirect_url': 'https://monarch.manage.com',
                'viewthrough_url': 'https://test.com',
                'destination_url': 'quitelongurllength',
                'ignore_fatigue_segment': False,
                'ignore_suppression_segment': False}
        self.assertEqual(self.call(data), {})

        data['ignore_fatigue_segment'] = True
        data['redirect_url'] = 'http://monarch.manage.com'
        self.assertEqual(self.call(data), {})

        data['ignore_fatigue_segment'] = False
        data['ignore_suppression_segment'] = False
        self.assertEqual(self.call(data), {'click url': 'insecure URL, use https://'})

        data['ignore_fatigue_segment'] = True
        data['viewthrough_url'] = 'htttp://test.com'
        self.assertEqual(self.call(data), {'impression url': 'insecure URL, use https://'})

        data['viewthrough_url'] = 'https://test.com'
        data['destination_url'] = 'short_url'
        self.assertEqual(self.call(data), {'destination_url': 'Must be at least {0} characters long'.format(self.serializer.DOMAIN_MIN_LENGTH)})

    def test__is_valid_genre__for_campaigns(self):
        self.set_callee('_is_valid_genre')

        data = {'genre': 1}
        self.assertEqual(self.call(data), {})

        data['genre'] = ''
        self.assertEqual(self.call(data), {'genre': 'Field is required'})

    def test__is_valid_app_classifications__for_campaigns(self):
        self.set_callee('_is_valid_app_classifications')

        data = {'app_install': True, 'manage_classification': True}
        self.assertEqual(self.call(data), {})

        data['manage_classification'] = False
        self.assertEqual(self.call(data), {'app classifications': 'Field is required if app install yes'})

    def test__is_valid_attribution_window__for_campaigns(self):
        self.set_callee('_is_valid_attribution_window')

        data = {'attribution_window': 10}
        self.assertEqual(self.call(data), {})

        data['attribution_window'] = -5
        self.assertEqual(self.call(data), {'attribution_window': 'Must be positive number'})

    @mock.patch.object(serializer, '_is_valid_frequency_map')
    @mock.patch.object(serializer, '_is_valid_no_distributions')
    @mock.patch.object(serializer, '_is_valid_flight_budget_data')
    @mock.patch.object(serializer, '_is_valid_domain')
    @mock.patch.object(serializer, '_is_valid_app_install')
    @mock.patch.object(serializer, '_is_valid_urls')
    @mock.patch.object(serializer, '_is_valid_priority')
    @mock.patch.object(serializer, '_is_valid_genre')
    @mock.patch.object(serializer, '_is_valid_app_classifications')
    @mock.patch.object(serializer, '_is_valid_base')
    @mock.patch.object(serializer, '_prepare_categories_data')
    @mock.patch.object(serializer, '_get_status')
    @mock.patch.object(serializer, '_is_valid_inflator')
    @mock.patch.object(serializer, '_is_valid_attribution_window')
    def test__is_valid__was_called(self,
                                   _is_valid_frequency_map,
                                   _is_valid_no_distributions,
                                   _is_valid_flight_budget_data,
                                   _is_valid_domain,
                                   _is_valid_app_install,
                                   _is_valid_urls,
                                   _is_valid_priority,
                                   _is_valid_genre,
                                   _is_valid_app_classifications,
                                   _is_valid_base,
                                   _prepare_categories_data,
                                   _is_valid_attribution_window,
                                   _get_status,
                                   _is_valid_inflator):

        test_serializer_method_calls = self.serializer(data={'advertiser_id':1}, context={'request': ''}, instance={})
        test_serializer_method_calls.is_valid()
        for method in self.CALL_METHODS:
            self.assertTrue(getattr(self.serializer, method).called)
