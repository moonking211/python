from django.http import HttpResponse
import json
from rest_framework import views
from rest_framework.response import Response
from restapi.models.User import User


MIN_PASSWORD_LENGTH = 6
MIN_PASSWORD_DIGITS = 1

DEBUG = False


def chars_count(string, chars):
    return len([c for c in string if c in chars])


class UserSetPassword(views.APIView):
    def dispatch(self, request, username, token):
        qs = User.objects_raw.filter(username=username)
        user = qs.first() if qs.exists() else None

        if DEBUG:
            print "user=%s;" % repr(user)

        if DEBUG and user is not None:
            print "user_token=%s;" % user.get_reset_password_hash()

        if user is None:
            return HttpResponse('{"HTTP-STATUS": 403}', status=200)

        if token != user.get_reset_password_hash():
            return HttpResponse('{"HTTP-STATUS": 400, "message": "Invalid token"}', status=200)

        return super(UserSetPassword, self).dispatch(request, user)

    def get(self, request, user):
        data = {'HTTP-STATUS': 200,
                'trading_desk': user.trading_desk,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username}
        return HttpResponse(json.dumps(data), status=200)

    def post(self, request, user):
        password = request.DATA.get('new_password', None)
        errors = []

        if password is None:
            errors.append('This field is required.')
        else:
            if len(password) < MIN_PASSWORD_LENGTH:
                errors.append('Please enter at least %s characters' % MIN_PASSWORD_LENGTH)

            if chars_count(password, [str(i) for i in xrange(10)]) < MIN_PASSWORD_DIGITS:
                errors.append('Please enter at least %s digits' % MIN_PASSWORD_DIGITS)

        if errors:
            data = {'HTTP-STATUS': 400,
                    'new_password': errors}
            return HttpResponse(json.dumps(data), status=200)

        user.set_password(password)
        user.save()
        return HttpResponse('{"HTTP-STATUS": 200}', status=200)
