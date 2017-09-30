# -*- coding: utf-8 -*-
import unittest

from pyparsing import ParseException

from tests.utils.grammar import get_record_grammar

"""
CWR Publisher For Writer grammar tests.

The following cases are tested:
"""

__author__ = 'Bernardo Martínez Garrido'
__license__ = 'MIT'
__status__ = 'Development'


class TestWriterPublisherGrammar(unittest.TestCase):
    """
    Tests that the Writer grammar decodes correctly formatted strings
    """

    def setUp(self):
        self.grammar = get_record_grammar('writer_publisher')

    def test_valid_full(self):
        """
        Tests that Writer grammar decodes correctly formatted record prefixes.

        This test contains all the optional fields.
        """
        record = 'PWR0000123400000023A12345678THE PUBLISHER                                C1234567890123D1234567890123A12345678'

        result = self.grammar.parseString(record)[0]

        self.assertEqual('PWR', result.record_type)
        self.assertEqual(1234, result.transaction_sequence_n)
        self.assertEqual(23, result.record_sequence_n)
        self.assertEqual('A12345678', result.publisher_ip_n)
        # self.assertEqual('THE PUBLISHER', result.publisher_name)
        self.assertEqual('C1234567890123', result.submitter_agreement_n)
        self.assertEqual('D1234567890123', result.society_assigned_agreement_n)
        self.assertEqual('A12345678', result.writer_ip_n)


class TestWriterPublisherGrammarException(unittest.TestCase):
    def setUp(self):
        self.grammar = get_record_grammar('writer_publisher')

    def test_empty(self):
        """
        Tests that a exception is thrown when the the works number is zero.
        """
        record = ''

        self.assertRaises(ParseException, self.grammar.parseString, record)

    def test_invalid(self):
        record = 'This is an invalid string'

        self.assertRaises(ParseException, self.grammar.parseString, record)
