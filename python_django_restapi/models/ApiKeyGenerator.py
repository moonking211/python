import hashlib
import random
import string
from django.conf import settings


class ApiKeyGenerator(object):

    @staticmethod
    def key_generator():
        gen_string = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(32))
        return hashlib.sha1(gen_string).hexdigest()

    @staticmethod
    def random_string(value):
        if settings.BINARY_FIELDS:
            return ''.join([chr(random.randint(0x01, 0xFF)) for _ in xrange(value)])
        else:
            return ''.join([random.choice(string.ascii_lowercase + string.digits) for _ in xrange(value)])

    @staticmethod
    def random_string_16():
        return ApiKeyGenerator.random_string(16)

    @staticmethod
    def random_string_4():
        return ApiKeyGenerator.random_string(4)
