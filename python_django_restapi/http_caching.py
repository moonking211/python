import hashlib
from django.db.models.signals import post_save, post_delete, post_init
from django.http.response import StreamingHttpResponse
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import resolve
from time import time

CACHE_TIMEOUT = 300

def _model_key(model):
    return "model-timestamp.{}".format(model.__name__)

def invalidate(model_name, pks=None):
    #TODO: invalidate cache by model_name and pk
    key = "model-timestamp.{}".format(model_name)
    timestamp = time()
    cache.set(key, timestamp)

class HTTPCaching(object):
    models = []

    models_init = set()
    models_save = set()
    
    @classmethod
    def register(cls, model_cls, *args, **kwargs):
        cls.models.append(model_cls)
        post_init.connect(cls.init_receiver, sender=model_cls)
        post_save.connect(cls.save_receiver, sender=model_cls)
        post_delete.connect(cls.save_receiver, sender=model_cls)

    @staticmethod
    def init_receiver(sender, instance, **kwargs):
        HTTPCaching.models_init.add(sender)

    @staticmethod
    def save_receiver(sender, instance, **kwargs):
        HTTPCaching.models_save.add(sender)
        invalidate(sender.__name__)


class HTTPCachingMiddleware(object):
    is_cached = None

    def _key(self, request):
        key = None
        if '_auth_user_id' in request.session:
            hashed_path = hashlib.md5(request.get_full_path()).hexdigest()
            key = "http-cache:{user_id}:{uri}".format(user_id=request.session['_auth_user_id'], uri=hashed_path)
        return key

    def get_cached_response(self, request):
        self.is_cached = False

        key = self._key(request)
        if not key:
            return None

        data = cache.get(key)
        if not data:
            return None

        for model in HTTPCaching.models_init:
            if not model.__name__ in data['models']:
                return None
            cache_timestamp = data['models'][model.__name__]

            model_timestamp = cache.get(_model_key(model))
            if model_timestamp and model_timestamp > cache_timestamp:
                return None

        self.is_cached = True
        return data['response']

    def set_cached_response(self, request, response):
        if self.is_cached:
            return

        key = self._key(request)
        if not key:
            return

        models = {}
        for model in HTTPCaching.models_init:
            models[model.__name__] = time()

        data = {'response': response,
                'models': models}

        cache.set(key, data, CACHE_TIMEOUT)

    def can_cache(self, request):
        if not settings.HTTP_CACHING:
            return False
        avail = False
        try:
            avail = request.resolver_match.kwargs['http_caching']
        except:
            pass
        return bool(avail)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not self.can_cache(request):
            return None

        response = None
        if request.method == 'GET':
            response = self.get_cached_response(request)
        return response

    def process_response(self, request, response):
        if self.can_cache(request) and request.method == 'GET' and not isinstance(response, StreamingHttpResponse):
            self.set_cached_response(request, response)
            response['X-Cached-Content'] = self.is_cached
        return response
