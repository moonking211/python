import json
from mock import Mock
from django.test import Client, TestCase
from restapi.models import User
from restapi.testspecs.CreateTestClient import CreateTestClient
from restapi.views.user.UserSetPassword import UserSetPassword

post = Mock()


class UserSetPasswordSpecs(TestCase, CreateTestClient):
    def setUp(self):
        self.client = Client()
        self.user_detail = UserSetPassword

    def test__class_methods__exists(self):
        self.assert_(hasattr(self.user_detail, 'dispatch'))
        self.assert_(hasattr(self.user_detail, 'get'))
        self.assert_(hasattr(self.user_detail, 'post'))

    def test__user_reset_password_get__return_correct_response(self):
        # arrange
        self._create_client()
        user = User.objects.get(username='user@mng.com')

        # act
        response = self.client.get('/set_password/{0}/{1}'.format(user.get_reset_password_hash(), user.username))

        # assert
        result = json.loads(response.content)
        self.assertEqual(result['username'], user.username)
        self.assertEqual(result['email'], user.email)

    def test__user_reset_password_post__reset_password(self):
        # arrange
        self._create_client()
        user = User.objects.get(username='user@mng.com')
        self.post_request = post
        self.post_request.DATA = {'new_password': 'test_password1'}

        # act
        response = self.client.post('/set_password/{0}/{1}'.format(user.get_reset_password_hash(), user.username),
                                    self.post_request.DATA)

        # assert
        self.assertEqual(response.status_code, 200)
