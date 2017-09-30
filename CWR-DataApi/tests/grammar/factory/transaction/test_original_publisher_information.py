# -*- coding: utf-8 -*-
import unittest

from pyparsing import ParseException

from tests.utils.grammar import get_record_grammar

"""
CWR Original Publisher Information grammar tests.

The following cases are tested:
"""

__author__ = 'Bernardo Martínez Garrido'
__license__ = 'MIT'
__status__ = 'Development'


class TestOriginalPublisherGrammar(unittest.TestCase):
    def setUp(self):
        self.grammar = get_record_grammar('original_publisher_information')

    def test_valid_full(self):
        publisher = 'SPU000012340000002319A12345678PUBLISHER NAME                                AQ92370341200014107338A0123456789123009020500100300001102312BY I-000000229-7A0123456789124A0123456789125OSB'
        npn = 'NPN000012340000002312A12345678THE NAME                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        ES'
        territory_1 = 'SPT0000123400000023A12345678      010120500002520I0008Y012'
        territory_2 = 'SPT0000123400000023A12345678      010120500002520I0008Y012'

        record = publisher + '\n' + npn + '\n' + territory_1 + '\n' + territory_2

        result = self.grammar.parseString(record)

        self.assertEqual(4, len(result))

        self.assertEqual('SPU', result[0].record_type)
        self.assertEqual('NPN', result[1].record_type)
        self.assertEqual('SPT', result[2].record_type)
        self.assertEqual('SPT', result[3].record_type)

    def test_territory_1(self):
        publisher = 'SPU000012340000002319A12345678PUBLISHER NAME                                AQ92370341200014107338A0123456789123009020500100300001102312BY I-000000229-7A0123456789124A0123456789125OSB'
        territory = 'SPT0000123400000023A12345678      010120500002520I0008Y012'

        record = publisher + '\n' + territory

        result = self.grammar.parseString(record)

        self.assertEqual(2, len(result))

        self.assertEqual('SPU', result[0].record_type)
        self.assertEqual('SPT', result[1].record_type)

    def test_territory_2(self):
        publisher = 'SPU000012340000002319A12345678PUBLISHER NAME                                AQ92370341200014107338A0123456789123009020500100300001102312BY I-000000229-7A0123456789124A0123456789125OSB'
        territory = 'SPT0000123400000023A12345678      010120500002520I0008Y012'

        record = publisher + '\n' + territory + '\n' + territory

        result = self.grammar.parseString(record)

        self.assertEqual(3, len(result))

        self.assertEqual('SPU', result[0].record_type)
        self.assertEqual('SPT', result[1].record_type)
        self.assertEqual('SPT', result[2].record_type)

    def test_nra(self):
        publisher = 'SPU000012340000002319A12345678PUBLISHER NAME                                AQ92370341200014107338A0123456789123009020500100300001102312BY I-000000229-7A0123456789124A0123456789125OSB'
        npn = 'NPN000012340000002312A12345678THE NAME                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        ES'

        record = publisher + '\n' + npn

        result = self.grammar.parseString(record)

        self.assertEqual(2, len(result))

        self.assertEqual('SPU', result[0].record_type)
        self.assertEqual('NPN', result[1].record_type)

    def test_valid_min(self):
        publisher = 'SPU000012340000002319A12345678PUBLISHER NAME                                AQ92370341200014107338A0123456789123009020500100300001102312BY I-000000229-7A0123456789124A0123456789125OSB'

        record = publisher

        result = self.grammar.parseString(record)

        self.assertEqual(1, len(result))

        self.assertEqual('SPU', result[0].record_type)


class TestOriginalPublisherGrammarException(unittest.TestCase):
    def setUp(self):
        self.grammar = get_record_grammar('original_publisher_information')

    def test_empty(self):
        """
        Tests that a exception is thrown when the the works number is zero.
        """
        record = ''

        self.assertRaises(ParseException, self.grammar.parseString, record)

    def test_invalid(self):
        record = 'This is an invalid string'

        self.assertRaises(ParseException, self.grammar.parseString, record)
