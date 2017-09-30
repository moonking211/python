from mock import Mock
from mng.test import spec
from restapi.views.Blobs import Blobs
from django.conf import settings


class BlobsSpecs(spec(Blobs)):
    subject = None
    create_file_storage = None
    file_storage = None
    request = None

    def before_each(self):
        settings.MNG_CDN = None

        self.file_storage = Mock()  # mock of AbstractFileStorage
        self.file_storage.upload_file_to_temp = Mock(return_value='file_id_1')
        self.file_storage.move_file_to_persistent_store = Mock(
            return_value={'path': '/a.txt', 'uri': 'http://cdn.io/a.txt', 'mime': 'text/plain'})
        self.create_file_storage = Mock(return_value=self.file_storage)
        self.subject = Blobs(create_file_storage=self.create_file_storage)

        request = Mock()
        input_file = Mock()
        input_file.name = 'a.txt'
        request.FILES = {'file': input_file}
        request.QUERY_PARAMS = {}
        self.request = request

    def test__post__saves_files_in_blob_storage_with_the_specified_output_prefix(self):
        # act
        self.request.QUERY_PARAMS = {'outputPrefix': 'abc'}
        self.subject.post(self.request)

        # assert
        self.create_file_storage.assert_called_once_with(domain='abc', using='monarch')

    def test__post__saves_files_in_blob_storage(self):
        # act
        self.subject.post(self.request)

        # assert
        self.create_file_storage.assert_called_once_with(using='monarch')
        self.file_storage.upload_file_to_temp.assert_called_once_with(self.request.FILES['file'], 'a.txt')
        self.file_storage.move_file_to_persistent_store('file_id_1')

    def test__post__returns_blob_info(self):

        response = self.subject.post(self.request)
        result = response.data

        self.assertEqual(result['path'], 'a.txt')
        self.assertEqual(result['mime'], 'text/plain')
        self.assertEqual(result['uri'], 'https://cdn.io/a.txt')

    def test__post__returns_blob_with_cdn_ulr(self):
        settings.MNG_CDN = 'http://cdn.manage.com/'

        response = self.subject.post(self.request)
        result = response.data

        self.assertEqual(result['path'], 'a.txt')
        self.assertEqual(result['mime'], 'text/plain')
        self.assertEqual(result['uri'], 'http://cdn.manage.com/a.txt')
