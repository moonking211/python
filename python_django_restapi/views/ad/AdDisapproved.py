import json
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions

from django.conf import settings

from googleapiclient.discovery import build
from oauth2client import client
import httplib2

VERSION = 'v1.4'


class AdDisapproved(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def post(self, request):
        data = request.DATA

        try:
            ad_id = long(data['ad_id'])
        # pylint: disable=broad-except
        except Exception:
            status = HTTP_400_BAD_REQUEST
        else:
            try:
                google_request = self.get_service().creatives().get(accountId=settings.ACCOUNT_ID,
                                                                    buyerCreativeId=ad_id)
                response = google_request.execute()
                status = HTTP_200_OK

            # pylint: disable=broad-except
            except Exception as exception:
                status = HTTP_500_INTERNAL_SERVER_ERROR
                response = json.loads(exception.content)

        return Response(response, status=status)

    # pylint: disable=unused-argument,no-self-use
    def get_service(self):
        credentials = client.OAuth2Credentials(settings.ACCESS_TOKEN,
                                               settings.CLIENT_ID,
                                               settings.CLIENT_SECRET,
                                               settings.REFRESH_TOKEN,
                                               settings.TOKEN_EXPIRY,
                                               settings.URI_TOKEN,
                                               settings.USER_AGENT)
        credentials.scopes = settings.SCOPE
        http = credentials.authorize(httplib2.Http())
        service = build(settings.SERVICE_NAME, VERSION, http=http)

        return service
