# -*- coding: utf-8 -*-
import unittest

from pyparsing import ParseException

from tests.utils.grammar import get_record_grammar

"""
CWR Administrator Information grammar tests.

The following cases are tested:
"""

__author__ = 'Bernardo Martínez Garrido'
__license__ = 'MIT'
__status__ = 'Development'


class TestGroupsGrammar(unittest.TestCase):
    def setUp(self):
        self.grammar = get_record_grammar('groups')

    def test_agreement_min(self):
        group1 = 'GRHAGR0000102.100130400001  ' + '\n' + \
                 _agreement_short() + '\n' + \
                 'GRT012340123456701234567             '

        record = group1

        result = self.grammar.parseString(record)

        self.assertEqual(1, len(result))

    def test_agreement_short(self):
        group1 = 'GRHAGR0000102.100130400001  ' + '\n' + \
                 _agreement_short() + '\n' + \
                 'GRT012340123456701234567'

        record = group1

        result = self.grammar.parseString(record)

        self.assertEqual(1, len(result))

    def test_2(self):
        group1 = 'GRHAGR0000102.100130400001  ' + '\n' + \
                 _agreement_short() + '\n' + \
                 'GRT012340123456701234567             '
        group2 = 'GRHNWR0000102.100130400001  ' + '\n' + \
                 _work_big() + '\n' + \
                 'GRT012340123456701234567             '

        record = group1 + '\n' + group2

        result = self.grammar.parseString(record)

        self.assertEqual(2, len(result))

    def test_2_short(self):
        group1 = 'GRHAGR0000102.100130400001  ' + '\n' + \
                 _agreement_short() + '\n' + \
                 'GRT012340123456701234567'
        group2 = 'GRHNWR0000102.100130400001  ' + '\n' + \
                 _work_big() + '\n' + \
                 'GRT012340123456701234567'

        record = group1 + '\n' + group2

        result = self.grammar.parseString(record)

        self.assertEqual(2, len(result))

        self.assertEqual(1, len(result[0].transactions))

        self.assertEqual(4, len(result[0].transactions[0]))

        self.assertEqual(1, len(result[1].transactions))

        self.assertEqual(10, len(result[1].transactions[0]))

    def test_2_short_mix(self):
        group1 = 'GRHAGR0000102.100130400001  ' + '\n' + \
                 _agreement_short() + '\n' + \
                 'GRT012340123456701234567'
        group2 = 'GRHNWR0000102.100130400001  ' + '\n' + \
                 _work_big() + '\n' + \
                 'GRT012340123456701234567'

        record = group1 + '\n' + group2

        result = self.grammar.parseString(record)

        self.assertEqual(2, len(result))

    def test_agreement_work_min(self):
        header = 'GRHAGR0000102.100130400001  '
        trailer = 'GRT012340123456701234567             '

        record = header + '\n' + _agreement_short() + '\n' + trailer

        result = self.grammar.parseString(record)[0]

        self.assertEqual('GRH', result.group_header.record_type)

        self.assertEqual('GRT', result.group_trailer.record_type)

        transaction = result.transactions[0]

        self.assertEqual('AGR', transaction[0].record_type)

    def test_two_agr_work(self):
        record = _two_groups_agr_work()

        result = self.grammar.parseString(record)

        self.assertEqual(2, len(result))

        group = result[0]

        self.assertEqual('GRH', group.group_header.record_type)

        self.assertEqual('GRT', group.group_trailer.record_type)

        self.assertEqual('AGR', group.group_header.transaction_type)

        transactions = group.transactions

        self.assertEqual(2, len(transactions))

        transaction = transactions[0]

        self.assertEqual(4, len(transaction))

        self.assertEqual('AGR', transaction[0].record_type)
        self.assertEqual('TER', transaction[1].record_type)
        self.assertEqual('IPA', transaction[2].record_type)
        self.assertEqual('IPA', transaction[3].record_type)

        transaction = transactions[1]

        self.assertEqual(4, len(transaction))

        self.assertEqual('AGR', transaction[0].record_type)
        self.assertEqual('TER', transaction[1].record_type)
        self.assertEqual('IPA', transaction[2].record_type)
        self.assertEqual('IPA', transaction[3].record_type)

        group = result[1]

        self.assertEqual('GRH', group.group_header.record_type)

        self.assertEqual('GRT', group.group_trailer.record_type)

        self.assertEqual('NWR', group.group_header.transaction_type)

        transactions = group.transactions

        self.assertEqual(2, len(transactions))

    def test_two_work_agr(self):
        record = _two_groups_work_agr()

        result = self.grammar.parseString(record)

        self.assertEqual(2, len(result))

        group = result[0]

        self.assertEqual('GRH', group.group_header.record_type)

        self.assertEqual('GRT', group.group_trailer.record_type)

        self.assertEqual('NWR', group.group_header.transaction_type)

        transactions = group.transactions

        self.assertEqual(2, len(transactions))

        group = result[1]

        self.assertEqual('GRH', group.group_header.record_type)

        self.assertEqual('GRT', group.group_trailer.record_type)

        self.assertEqual('AGR', group.group_header.transaction_type)

        transactions = group.transactions

        self.assertEqual(2, len(transactions))

        transaction = transactions[0]

        self.assertEqual(4, len(transaction))

        self.assertEqual('AGR', transaction[0].record_type)
        self.assertEqual('TER', transaction[1].record_type)
        self.assertEqual('IPA', transaction[2].record_type)
        self.assertEqual('IPA', transaction[3].record_type)

        transaction = transactions[1]

        self.assertEqual(4, len(transaction))

        self.assertEqual('AGR', transaction[0].record_type)
        self.assertEqual('TER', transaction[1].record_type)
        self.assertEqual('IPA', transaction[2].record_type)
        self.assertEqual('IPA', transaction[3].record_type)


class TestGroupsGrammarException(unittest.TestCase):
    def setUp(self):
        self.grammar = get_record_grammar('transactions')

    def test_empty(self):
        record = ''

        self.assertRaises(ParseException, self.grammar.parseString, record)

    def test_invalid(self):
        record = 'This is an invalid string'

        self.assertRaises(ParseException, self.grammar.parseString, record)


def _agreement_short():
    agr_1 = 'AGR000000000000000000023683606100              OS200311182013111820131118N        D20131118        00009SYY              '
    ter_1_1 = 'TER0000000000000000I2136'
    ipa_1_1 = 'IPA0000000000000001AS0026166137500000000000001183606  ITALIAN                                      GILBERTI DUANTE               61 0500061 0000061 00000'
    ipa_1_2 = 'IPA0000000000000002AC00250165006000000000000066       SOCIETY MUSIC                                                              61 0500061 1000061 10000'

    return agr_1 + '\n' + ter_1_1 + '\n' + ipa_1_1 + '\n' + ipa_1_2


def _work_big():
    return 'NWR0000019900000000WORK NAME                                                     1450455                  00000000            UNC000000YMTX   ORI   ORIORI                                          N00000000000U                                                  Y' + '\n' + \
           'SPU0000019900000702014271370  MUSIC SOCIETY                                 E          005101734040102328568410061 0500061 1000061 10000   0000000000000                            OS ' + '\n' + \
           'SPU00000199000007030166       ANOTHER SOCIETY                               AM         002501650060477617137010061 0000061 0000061 00000   0000000000000                            PS ' + '\n' + \
           'SPU00000199000007040170       YET ANOTHER SOCIETY                           SE         002261445930035870006610059 00000   00000   00000   0000000000000                            PG ' + '\n' + \
           'SPT000001990000070570             050000500005000I0484Y001' + '\n' + \
           'SWR00000199000007061185684  A NAME                                       YET ANOTHER NAME               C          0026058307861 0500061 0000061 00000    0000260582865             ' + '\n' + \
           'SWT00000199000007071185684  050000500005000I0484Y001' + '\n' + \
           'PWR00000199000007084271370  MUSIC SOCIETY                                01023285684100              1185684  ' + '\n' + \
           'PER0000019900000709A NAME                                                                     000000000000000000000000' + '\n' + \
           'REC000001990000071019980101                                                            000300     A COMPILATION                                               P A I  _AR_                                                 33002                                       U   '


def _agr():
    agr = 'AGR000000000000000000023683606100              OS200311182013111820131118N        D20131118        00009SYY              '
    territory = 'TER0000000000000000I2136'
    ipa_1 = 'IPA0000000000000001AS0026166137500000000000001183606  ITALIAN                                      GILBERTI DUANTE               61 0500061 0000061 00000'
    ipa_2 = 'IPA0000000000000002AC00250165006000000000000066       SOCIETY MUSIC                                                              61 0500061 1000061 10000'

    return agr + '\n' + territory + '\n' + ipa_1 + '\n' + ipa_2


def _work():
    transaction2 = 'NWR0000019900000000WORK NAME                                                     1450455                  00000000            UNC000000YMTX   ORI   ORIORI                                          N00000000000U                                                  Y' + '\n' + \
                   'SPU0000019900000702014271370  MUSIC SOCIETY                                 E          005101734040102328568410061 0500061 1000061 10000   0000000000000                            OS ' + '\n' + \
                   'SPU00000199000007030166       ANOTHER SOCIETY                               AM         002501650060477617137010061 0000061 0000061 00000   0000000000000                            PS ' + '\n' + \
                   'SPU00000199000007040170       YET ANOTHER SOCIETY                           SE         002261445930035870006610059 00000   00000   00000   0000000000000                            PG ' + '\n' + \
                   'SPT000001990000070570             050000500005000I0484Y001' + '\n' + \
                   'SWR00000199000007061185684  A NAME                                       YET ANOTHER NAME               C          0026058307861 0500061 0000061 00000    0000260582865             ' + '\n' + \
                   'SWT00000199000007071185684  050000500005000I0484Y001' + '\n' + \
                   'PWR00000199000007084271370  MUSIC SOCIETY                                01023285684100              1185684  ' + '\n' + \
                   'PER0000019900000709A NAME                                                                     000000000000000000000000' + '\n' + \
                   'REC000001990000071019980101                                                            000300     A COMPILATION                                               P A I  _AR_                                                 33002                                       U   '

    return transaction2


def _two_groups_agr_work():
    header_agr = 'GRHAGR0000102.100130400001  '
    trailer_agr = 'GRT000010000017900000719   0000000000'

    header_work = 'GRHNWR0000102.100130400001  '
    trailer_work = 'GRT000010000017900000719   0000000000'

    record = header_agr + '\n' + \
             _agr() + '\n' + \
             _agr() + '\n' + \
             trailer_agr + '\n' + \
             header_work + '\n' + \
             _work() + '\n' + \
             _work() + '\n' + \
             trailer_work + '\n'

    return record


def _two_groups_work_agr():
    header_agr = 'GRHAGR0000102.100130400001  '
    trailer_agr = 'GRT000010000017900000719   0000000000'

    header_work = 'GRHNWR0000102.100130400001  '
    trailer_work = 'GRT000010000017900000719   0000000000'

    record = header_work + '\n' + \
             _work() + '\n' + \
             _work() + '\n' + \
             trailer_work + '\n' + \
             header_agr + '\n' + \
             _agr() + '\n' + \
             _agr() + '\n' + \
             trailer_agr + '\n'

    return record
