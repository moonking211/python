import json
from rest_framework.views import exception_handler as default_exception_handler
from rest_framework.serializers import ValidationError


def exception_handler(exc, context):
    response = default_exception_handler(exc, context)
    if isinstance(exc, ValidationError) and isinstance(exc.detail, list):
        content = {'validation_errors': exc.detail, 'HTTP-STATUS': exc.status_code}
        response.content = json.dumps(content)
        response.status_code = 200
    return response
