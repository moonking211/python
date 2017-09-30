from sys import maxint
from mock import Mock
from mng.test import spec
from restapi.views.pagination.ListPagination import ListPagination


class ListPaginationSpecs(spec(ListPagination)):
    request = None
    subject = None

    def before_each(self):
        self.request = Mock()
        self.request.query_params = {}
        self.subject = ListPagination()
        self.subject.request = self.request
        self.subject.page = Mock()
        self.subject.page.paginator = Mock()
        self.subject.page.paginator.count = 12

    def test__get_paginated_response__returns_wrapped_data_argument(self):
        # act
        ret = self.subject.get_paginated_response('result1')

        # assert
        assert ret.data['count'] == 1
        assert ret.data['total'] == 12
        assert ret.data['results'] == 'result1'

    def test__get_page_size__returns_maxint_when_page_size_value_from_query_string_is_zero(self):
        # act
        self.request.query_params = {u'$page_size': u'0'}
        ret = self.subject.get_page_size(self.request)

        # assert
        assert ret == maxint
