from mock import Mock

from mng.test import spec
from restapi.views.filters.FilterByListMixin import FilterByListMixin


class FilterByListMixinSpecs(spec(FilterByListMixin)):
    subject = None
    request = None

    def before_each(self):
        self.request = Mock()
        self.request.query_params = {}
        self.subject = FilterByListMixin()
        self.subject.queryset = Mock()
        self.subject.queryset.values = Mock(return_value='value_query_set')
        self.subject.request = self.request

    def test__get_queryset__applies_select_query_string_argument_and_returns_value_query_set(self):
        # pylint: disable=unnecessary-pass
        pass
        #FIXME: NEED to fix test
        # pylint: disable=pointless-string-statement
        '''self.request.query_params['$select'] = u'field1,field2'
        query_set = self.subject.get_queryset()

        # assert
        self.subject.queryset.values.assert_called_with(u'field1', u'field2')
        print (query_set)
        assert query_set == 'value_query_set'
        '''
