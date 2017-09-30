# encoding: utf-8
from __future__ import unicode_literals

#pylint: disable=no-self-use
import json

import cProfile
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import MiddlewareNotUsed
from django.db import connection
from django.http import HttpResponse
from io import BytesIO
import pstats
from restapi.registry import REGISTRY
from restapi.models import Advertiser
from restapi.models.Agency import Agency
from restapi.models.User import User
from restapi.models.TradingDesk import TradingDesk
from restapi.debug import logger, extra


FORBIDDEN = 403

CACHE_TIME = 60  # 1 minute


class DisableCSRF(object):
    def process_request(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)


class JsonHttpStatusCode(object):
    # pylint: disable=unused-argument
    def process_response(self, request, response):
        content_type = response.get('Content-Type', None)
        status_code = response.status_code

        if content_type == 'application/json':
            try:
                content = response.content
                content_json = json.loads(content)
                content_json['HTTP-STATUS'] = status_code
                content = json.dumps(content_json)
                response.content = content
                # TODO(victor): we should not always set status to 200 OK.
                # response.status_code = 200
            except TypeError:
                pass

        return response


class PreAuthentication(object):
    def process_request(self, request):
        User._default_manager = User.objects_raw


class Authentication(object):
    def process_request(self, request):
        logger.debug('', extra=extra(request))
        user = request.user
        REGISTRY['user'] = user

        user_trading_desk_ids = []
        user_agency_ids = []
        user_advertiser_ids = []
        if user.is_authenticated():
            CACHE_KEY = "restapi:%s:user_own_ids" % user.pk
            own_ids = cache.get(CACHE_KEY)
            if not own_ids or not CACHE_TIME:
                own_ids = {}
                trading_desks = TradingDesk.objects_raw.filter(trading_desk_userprofiles__user=user)
                own_ids['trading_desk'] = [r.pk for r in trading_desks]
                user_advertiser_ids = list(Advertiser.Advertiser.objects_raw.filter(
                    advertiser_userprofiles__user=user
                ).values_list('advertiser_id', flat=True))
                own_ids['advertiser'] = user_advertiser_ids
                agencies = Agency.objects_raw.filter(trading_desk_id_id__in=user_trading_desk_ids)
                own_ids['agency'] = [r.pk for r in agencies]

                cache.set(CACHE_KEY, own_ids, CACHE_TIME)

            user_trading_desk_ids = own_ids['trading_desk']
            user_advertiser_ids = own_ids['advertiser']
            user_agency_ids = own_ids['agency']

        REGISTRY['user_trading_desk_ids'] = user_trading_desk_ids
        REGISTRY['user_advertiser_ids'] = user_advertiser_ids
        REGISTRY['user_agency_ids'] = user_agency_ids

        for attr in ['_perm_cache', '_group_perm_cache']:
            if hasattr(user, attr):
                delattr(user, attr)


class Profiling(object):
    def __init__(self):
        if not settings.DEBUG:
            raise MiddlewareNotUsed()
        self.profiler = None
        self.time_start = datetime.now()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        self.profiler = cProfile.Profile()
        args = (request,) + callback_args
        return self.profiler.runcall(callback, *args, **callback_kwargs)

    def process_response(self, request, response):
        if 'profiling' in request.GET:
            stats = [self._stats_db(),
                     self._stats_calls()]

            content = ("\n\n%s\n\n" % ('-' * 80)).join(stats)

            response = HttpResponse()
            response.content = content
            response['Content-type'] = 'text/plain'
        return response

    def _stats_db(self):
        total_time = 0
        query_info = []
        get_time = lambda q: float(q.get('time') or q.get('duration', 0))
        for query in sorted(connection.queries, key=lambda q: -get_time(q)):
            query_time = get_time(query)
            total_time += float(query_time)
            query_info.append('%s. %ss : %s\n' % (len(query_info)+1,
                                                query_time,
                                                query.get('sql')))

        total_count = len(connection.queries)
        total_time = round(total_time, 3)
        total_info = "Total DB queries: %s in %ss\n" % (total_count, total_time)

        info = "\n".join([total_info, ''] + query_info)
        return info

    def _stats_calls(self):
            self.profiler.create_stats()
            out = BytesIO()
            stats = pstats.Stats(self.profiler, stream=out)
            stats.sort_stats('time').print_stats(0.1)
            return out.getvalue()
