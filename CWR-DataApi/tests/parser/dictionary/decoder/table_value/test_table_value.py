# -*- coding: utf-8 -*-

import unittest

from cwr.parser.decoder.dictionary import TableValueDictionaryDecoder

"""
Dictionary to Message decoding tests.

The following cases are tested:
"""

__author__ = 'Bernardo Martínez Garrido'
__license__ = 'MIT'
__status__ = 'Development'


class TestTableValueDecoder(unittest.TestCase):
    def setUp(self):
        self._decoder = TableValueDictionaryDecoder()

    def test_encoded(self):
        data = {}

        data['code'] = 'AS'
        data['name'] = 'Assignor'
        data[
            'description'] = 'The entitled party who is assigning the rights to a musical work within an agreement'

        record = self._decoder.decode(data)

        self.assertEqual('AS', record.code)
        self.assertEqual('Assignor', record.name)
        self.assertEqual(
            'The entitled party who is assigning the rights to a musical work within an agreement',
            record.description)
