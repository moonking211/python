# -*- coding: utf-8 -*-
import unittest

from pyparsing import ParseException

from tests.utils.grammar import get_record_grammar

"""
CWR Component grammar tests.

The following cases are tested:
"""

__author__ = 'Bernardo Martínez Garrido'
__license__ = 'MIT'
__status__ = 'Development'


class TestComponentGrammar(unittest.TestCase):
    """
    Tests that the NWN grammar decodes correctly formatted strings
    """

    def setUp(self):
        self.grammar = get_record_grammar('component')

    def test_valid_full(self):
        """
        Tests that NWN grammar decodes correctly formatted record prefixes.

        This test contains all the optional fields.
        """
        record = 'COM0000123400000023THE TITLE                                                   T0123456789ABCD0123456789030201LAST NAME 1                                  FIRST NAME 1                  00014107338LAST NAME 2                                  FIRST NAME 2                  00014107339I-000000229-7I-000000230-7'

        result = self.grammar.parseString(record)[0]

        self.assertEqual('COM', result.record_type)
        self.assertEqual(1234, result.transaction_sequence_n)
        self.assertEqual(23, result.record_sequence_n)
        self.assertEqual('THE TITLE', result.title)
        self.assertEqual('T0123456789', result.iswc)
        self.assertEqual('ABCD0123456789', result.submitter_work_n)
        self.assertEqual(3, result.duration.hour)
        self.assertEqual(2, result.duration.minute)
        self.assertEqual(1, result.duration.second)
        self.assertEqual('LAST NAME 1', result.writer_1_last_name)
        self.assertEqual('FIRST NAME 1', result.writer_1_first_name)
        self.assertEqual(14107338, result.writer_1_ipi_name_n)
        self.assertEqual('LAST NAME 2', result.writer_2_last_name)
        self.assertEqual('FIRST NAME 2', result.writer_2_first_name)
        self.assertEqual(14107339, result.writer_2_ipi_name_n)
        self.assertEqual('I-000000229-7', result.writer_1_ipi_base_n)
        self.assertEqual('I-000000230-7', result.writer_2_ipi_base_n)


class TestComponentGrammarException(unittest.TestCase):
    def setUp(self):
        self.grammar = get_record_grammar('work_alternate_title')

    def test_empty(self):
        """
        Tests that a exception is thrown when the the works number is zero.
        """
        record = ''

        self.assertRaises(ParseException, self.grammar.parseString, record)

    def test_invalid(self):
        record = 'This is an invalid string'

        self.assertRaises(ParseException, self.grammar.parseString, record)
