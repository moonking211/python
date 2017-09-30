# -*- coding: utf-8 -*-
import unittest

from pyparsing import ParseException

from tests.utils.grammar import get_record_grammar

"""
CWR Non-Roman Alphabet Title grammar tests.

The following cases are tested:
"""

__author__ = 'Bernardo Martínez Garrido'
__license__ = 'MIT'
__status__ = 'Development'


class TestNPAGrammar(unittest.TestCase):
    """
    Tests that the NPA grammar decodes correctly formatted strings
    """

    def setUp(self):
        self.grammar = get_record_grammar('nra_title')

    def test_valid_full(self):
        """
        Tests that IPA grammar decodes correctly formatted record prefixes.

        This test contains all the optional fields.
        """
        record = 'NAT0000123400000023THE TITLE                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       ATES'

        result = self.grammar.parseString(record)[0]

        self.assertEqual('NAT', result.record_type)
        self.assertEqual(1234, result.transaction_sequence_n)
        self.assertEqual(23, result.record_sequence_n)
        self.assertEqual('THE TITLE', result.title)
        self.assertEqual('AT', result.title_type)
        self.assertEqual('ES', result.language_code)

    def test_extended_character(self):
        """
        Tests that IPA grammar decodes correctly formatted record prefixes.

        This test contains all the optional fields.
        """
        record = 'NAT0000123400000023THE TITLE \xc6\x8f                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ATES'

        result = self.grammar.parseString(record)[0]

        self.assertEqual('NAT', result.record_type)
        self.assertEqual(1234, result.transaction_sequence_n)
        self.assertEqual(23, result.record_sequence_n)
        self.assertEqual('THE TITLE \xc6\x8f', result.title)
        self.assertEqual('AT', result.title_type)
        self.assertEqual('ES', result.language_code)


class TestNPAGrammarException(unittest.TestCase):
    def setUp(self):
        self.grammar = get_record_grammar('nra_title')

    def test_empty(self):
        """
        Tests that a exception is thrown when the the works number is zero.
        """
        record = ''

        self.assertRaises(ParseException, self.grammar.parseString, record)

    def test_invalid(self):
        record = 'This is an invalid string'

        self.assertRaises(ParseException, self.grammar.parseString, record)
