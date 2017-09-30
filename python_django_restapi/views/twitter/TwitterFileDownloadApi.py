from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import os
from django.http import Http404


class TwitterFileDownloadApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        file_name = request.query_params.get('file_name')
        if file_name:
            full_path = os.path.join('/tmp/tw_campaign_excels', file_name)
            if os.path.isfile(full_path):
                excel_file = open(full_path, 'rb')
                response = HttpResponse(FileWrapper(excel_file), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="%s"' % file_name
                return response

        raise Http404