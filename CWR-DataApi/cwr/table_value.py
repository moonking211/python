# -*- coding: utf-8 -*-

"""
Table value entity model classes.

These represent the values for the Table Lookup fields.
"""

__author__ = 'Bernardo Martínez Garrido, Borja Garrido Bear'
__license__ = 'MIT'
__status__ = 'Development'


class MediaTypeValue(object):
    """
    Represents a BIEM/CISAC Media Type table value.
    """

    def __init__(self,
                 code='',
                 name='',
                 media_type=None,
                 duration_max=0,
                 works_max=0,
                 fragments_max=0
                 ):
        self._code = code
        self._name = name
        self._media_type = media_type
        self._duration_max = duration_max
        self._works_max = works_max
        self._fragments_max = fragments_max

    @property
    def code(self):
        """
        The value code. String.

        :return: code for the value
        """
        return self._code

    @code.setter
    def code(self, value):
        self._code = value

    @property
    def duration_max(self):
        """
        Maximum duration of the media. Integer.

        :return: the maximum duration of the media
        """
        return self._duration_max

    @duration_max.setter
    def duration_max(self, value):
        self._duration_max = value

    @property
    def fragments_max(self):
        """
        Maximum number of fragments for the media. Integer.

        :return: the maximum number of fragments for the media
        """
        return self._fragments_max

    @fragments_max.setter
    def fragments_max(self, value):
        self._fragments_max = value

    @property
    def media_type(self):
        """
        Type of media.

        This is the group under which this media is. For example Vynil, Compact
        Disc or DVD.

        :return: the type of the media
        """
        return self._media_type

    @media_type.setter
    def media_type(self, value):
        self._media_type = value

    @property
    def name(self):
        """
        The value name. String.

        :return: value name
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def works_max(self):
        """
        Maximum number of works for the media. Integer.

        :return: the maximum number of works for the media
        """
        return self._works_max

    @works_max.setter
    def works_max(self, value):
        self._works_max = value


class TableValue(object):
    """
    Represents a CWR table value.

    Most of the values of the Table Lookup type use this object.

    This is a representation of general values such as musical genres, or the
    roles a party can take in an agreement.

    Some examples are:

    Agreement roles:
    Assignor (AS): The entitled party who is assigning the rights to a musical
    work within an agreement
    Acquirer (AC): The entitled party who is acquiring the rights to a musical
    work within an agreement

    Music arrangement:
    New (NEW): New music added to existing music
    Addition (ADM): Music added to a pre-existing text
    Original (ORI): Music used in its original form

    Text-Music relationship:
    Music (MUS): Music only
    Music and Text (MTX): Music and text combined
    Text (TXT): Self explanatory
    """

    def __init__(self,
                 code='',
                 name='',
                 description=''
                 ):
        self._code = code
        self._name = name
        self._description = description

    @property
    def code(self):
        """
        The value code. String.

        :return: code for the value
        """
        return self._code

    @code.setter
    def code(self, value):
        self._code = value

    @property
    def description(self):
        """
        Value description. String.

        :return: the value description
        """
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def name(self):
        """
        The value name. String.

        :return: value name
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = value


class InstrumentValue(TableValue):
    """
    Represents a Instrument table value.
    """

    def __init__(self,
                 code='',
                 name='',
                 family=None,
                 description=''
                 ):
        super(InstrumentValue, self).__init__(
            code,
            name,
            description
        )
        self._family = family

    @property
    def family(self):
        """
        The instrument family.

        :return: the family of the instrument
        """
        return self._family

    @family.setter
    def family(self, value):
        self._family = value
