from datetime import datetime
from django.test import TestCase
from pytz import UTC
from restapi.time_shifting import PacificTimeShift


class TimeShiftingTestCase(TestCase):
    def setUp(self):
        self.time_shift = PacificTimeShift

    def test__class_methods__exists(self):
        self.assert_(hasattr(self.time_shift, 'get'))
        self.assert_(hasattr(self.time_shift, 'get_for_db'))

    def test__get_method__return_time_shift(self):
        # arrange
        date = datetime.now(UTC)
        test_start_date = date.replace(month=5)
        test_finish_date = date.replace(month=12)

        # act
        result_start_date = self.time_shift.get(test_start_date)
        result_finish_date = self.time_shift.get(test_finish_date)

        # assert
        self.assertEquals(result_start_date, -7)
        self.assertEquals(result_finish_date, -8)

