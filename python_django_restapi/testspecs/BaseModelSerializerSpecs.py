from mock import Mock
from rest_framework import serializers
from mng.test import spec
from restapi.serializers.BaseModelSerializer import BaseModelSerializer


class BaseModelSerializerSpecs(spec(BaseModelSerializer)):
    subject = None
    request = None

    def before_each(self):
        self.request = Mock()
        self.request.QUERY_PARAMS = {}
        self.subject = BaseModelSerializer()
        self.subject.context['request'] = self.request
        self.stub(serializers.ModelSerializer).get_fields().thenReturn({u'field1': Mock(), u'field2': Mock()})

    def test__get_fields__returns_fields_specified_by_the_select_query_string_parameter(self):
        # act
        self.request.QUERY_PARAMS['$select'] = u'field1'
        fields = self.subject.get_fields()

        # assert
        assert len(fields.items()) == 1
        assert fields.items()[0][0] == u'field1'

    def test__get_fields__returns_all_fields_unless_select_query_string_parameter_is_provided(self):
        # act
        fields = self.subject.get_fields()

        # insert
        assert len(fields.items()) == 2
