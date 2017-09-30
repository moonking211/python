# -*- coding: utf-8 -*-
import unittest

from pyparsing import ParseException

from cwr.grammar.field import basic

"""
Tests for Boolean (B) fields.
"""

__author__ = 'Bernardo Martínez Garrido'
__license__ = 'MIT'
__status__ = 'Development'


class TestFlagName(unittest.TestCase):
    def test_name_default(self):
        """
        Tests that the default field name is correct for optional fields.
        """
        field = basic.flag()

        self.assertEqual('Flag Field', field.name)

    def test_name_set(self):
        """
        Tests that the given field name is set correctly for optional fields.
        """
        name = "Field Name"
        field = basic.flag(name=name)

        self.assertEqual(name, field.name)

        self.assertEqual(name, field.name)

    def test_name_set_no_changes(self):
        """
        Tests that the field name does not change for creating a new one
        """
        field1 = basic.flag(name='field1')
        field2 = basic.flag(name='field2')

        self.assertEqual('field1', field1.name)
        self.assertEqual('field2', field2.name)


class TestFlagValid(unittest.TestCase):
    """
    Tests that the flag field accepts and parses valid values.
    """

    def setUp(self):
        self.flag = basic.flag()

    def test_true(self):
        """
        Tests that the flag field accepts true ('Y').
        """
        result = self.flag.parseString('Y')
        self.assertEqual('Y', result[0])

    def test_false(self):
        """
        Tests that the flag field accepts false ('N').
        """
        result = self.flag.parseString('N')
        self.assertEqual('N', result[0])

    def test_unknown(self):
        """
        Tests that the flag field accepts unknown ('U').
        """
        result = self.flag.parseString('U')
        self.assertEqual('U', result[0])


class TestFlagException(unittest.TestCase):
    """
    Tests that exceptions are thrown when using invalid values
    """

    def setUp(self):
        self.flag = basic.flag()

    def test_true_lower(self):
        """
        Tests that an exception is thrown when the true code is in lower letters.
        """
        self.assertRaises(ParseException, self.flag.parseString, 'y')

    def test_false_lower(self):
        """
        Tests that an exception is thrown when the false code is in lower letters.
        """
        self.assertRaises(ParseException, self.flag.parseString, 'n')

    def test_unknown_lower(self):
        """
        Tests that an exception is thrown when the unknown code is in lower letters.
        """
        self.assertRaises(ParseException, self.flag.parseString, 'u')

    def test_empty(self):
        """
        Tests that an exception is thrown when the string is empty.
        """
        self.assertRaises(ParseException, self.flag.parseString, '')

    def test_whitespace(self):
        """
        Tests that an exception is thrown when the string is a whitespace.
        """
        self.assertRaises(ParseException, self.flag.parseString, ' ')
