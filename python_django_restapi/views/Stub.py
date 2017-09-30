from django.conf import settings
from rest_framework import views
from rest_framework.response import Response


class Stub(views.APIView):
    # pylint: disable=no-self-use
    def get(self, request, name, content_type=None):
        method = request.method
        if name not in settings.STUB:
            raise Exception("'%s' stub have no configuration" % name)
        stub = settings.STUB[name]
        if method not in stub:
            raise Exception("'%s' stub have no configuration for %s method" % (name, method))
        data = stub[method]
        response = Response(data)
        if content_type is not None:
            response.content_type = content_type
        return response
    post = put = get
