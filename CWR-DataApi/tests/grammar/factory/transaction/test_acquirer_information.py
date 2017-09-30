# -*- coding: utf-8 -*-
import unittest

from pyparsing import ParseException

from tests.utils.grammar import get_record_grammar

"""
CWR Acquirer Information grammar tests.

The following cases are tested:
"""

__author__ = 'Bernardo Martínez Garrido'
__license__ = 'MIT'
__status__ = 'Development'


class TestAcquirerInformationGrammar(unittest.TestCase):
    def setUp(self):
        self.grammar = get_record_grammar('ipa_information')

    def test_valid_full(self):
        ipa = 'IPA0000123400000023AC01234567890I-000000229-7A12345678LAST NAME                                    FIRST NAME                    009020500100300001102312'
        npa = 'NPA0000123400000023012345678PARTY NAME                                                                                                                                                      PARTY WRITER NAME                                                                                                                                               ES'

        record = ipa + '\n' + npa

        result = self.grammar.parseString(record)

        self.assertEqual(2, len(result))

        self.assertEqual('IPA', result[0].record_type)
        self.assertEqual('NPA', result[1].record_type)

    def test_min(self):
        ipa = 'IPA0000123400000023AC01234567890I-000000229-7A12345678LAST NAME                                    FIRST NAME                    009020500100300001102312'

        record = ipa

        result = self.grammar.parseString(record)

        self.assertEqual(1, len(result))

        self.assertEqual('IPA', result[0].record_type)


class TestAcquirerInformationGrammarException(unittest.TestCase):
    def setUp(self):
        self.grammar = get_record_grammar('ipa_information')

    def test_two_ipa(self):
        ipa = 'IPA0000123400000023AC01234567890I-000000229-7A12345678LAST NAME                                    FIRST NAME                    009020500100300001102312'

        record = ipa + '\n' + ipa

        result = self.grammar.parseString(record)

        self.assertEqual(1, len(result))

    def test_empty(self):
        """
        Tests that a exception is thrown when the the works number is zero.
        """
        record = ''

        self.assertRaises(ParseException, self.grammar.parseString, record)

    def test_invalid(self):
        record = 'This is an invalid string'

        self.assertRaises(ParseException, self.grammar.parseString, record)
