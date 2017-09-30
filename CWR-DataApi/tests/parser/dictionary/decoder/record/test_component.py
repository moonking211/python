# -*- coding: utf-8 -*-

import unittest
import datetime

from cwr.parser.decoder.dictionary import ComponentDictionaryDecoder
from cwr.other import ISWCCode

"""
Dictionary to Message decoding tests.

The following cases are tested:
"""

__author__ = 'Bernardo Martínez Garrido'
__license__ = 'MIT'
__status__ = 'Development'


class TestComponentDictionaryDecoder(unittest.TestCase):
    def setUp(self):
        self._decoder = ComponentDictionaryDecoder()

    def test_encoded(self):
        data = {}

        data['record_type'] = 'COM'
        data['transaction_sequence_n'] = 3
        data['record_sequence_n'] = 15
        data['title'] = 'TITLE'
        data['submitter_work_n'] = 'ABCD123'
        data['writer_1_last_name'] = 'LAST NAME 1'
        data['writer_1_first_name'] = 'FIRST NAME 1'
        data['writer_2_last_name'] = 'LAST NAME 2'
        data['writer_2_first_name'] = 'FIRST NAME 2'
        data['writer_1_ipi_name_n'] = 14107338
        data['writer_1_ipi_base_n'] = 'I-000000229-7'
        data['writer_2_ipi_name_n'] = 14107400
        data['writer_2_ipi_base_n'] = 'I-000000339-7'
        data['iswc'] = ISWCCode(12345678, 9)
        data['duration'] = datetime.datetime.strptime('011200', '%H%M%S').time()

        record = self._decoder.decode(data)

        self.assertEqual('COM', record.record_type)
        self.assertEqual(3, record.transaction_sequence_n)
        self.assertEqual(15, record.record_sequence_n)
        self.assertEqual('TITLE', record.title)
        self.assertEqual('LAST NAME 1', record.writer_1_last_name)
        self.assertEqual('ABCD123', record.submitter_work_n)
        self.assertEqual('FIRST NAME 1', record.writer_1_first_name)
        self.assertEqual('FIRST NAME 2', record.writer_2_first_name)
        self.assertEqual('LAST NAME 2', record.writer_2_last_name)
        self.assertEqual('LAST NAME 2', record.writer_2_last_name)
        self.assertEqual(14107338, record.writer_1_ipi_name_n)
        self.assertEqual(14107400, record.writer_2_ipi_name_n)
        self.assertEqual(12345678, record.iswc.id_code)
        self.assertEqual(9, record.iswc.check_digit)
        self.assertEqual(datetime.datetime.strptime('011200', '%H%M%S').time(),
                         record.duration)

        self.assertEqual('I-000000229-7', record.writer_1_ipi_base_n)

        self.assertEqual('I-000000339-7', record.writer_2_ipi_base_n)
