from rest_framework.response import Response
from rest_framework import generics
from restapi.registry import REGISTRY


class ConfigView(generics.GenericAPIView):
    def get_data(self):
        with open('config/local_settings.py', 'r') as file:
            return file.read()

    def get(self, request, **kwargs):
        data = self.get_data() if self.__check_read_permissions() else 'Permission Error'
        return Response({'results': data})

    def __check_read_permissions(self):
        user = REGISTRY['user']
        if not 'restapi.tools.any.read.show_config' in user.get_all_permissions():
            return False
        return True
