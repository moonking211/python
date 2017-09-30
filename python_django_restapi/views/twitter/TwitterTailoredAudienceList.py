import json
import urlparse
import urllib

from django.conf import settings
from django.core.cache import cache as redis_cache
from django.utils.http import int_to_base36

from rest_framework.response import Response
from rest_framework import status

from twitter_ads.client import Client
from twitter_ads.http import TONUpload
from twitter_ads.cursor import Cursor
from twitter_ads.http import Request
from twitter_ads.error import Error

from restapi.models.twitter.TwitterTailoredAudience import TwitterTailoredAudience
from restapi.serializers.twitter.TwitterTailoredAudienceSerializer import TwitterTailoredAudienceSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate
from restapi.models.twitter.TwitterAccount import TwitterAccount


class TwitterTailoredAudienceList(BaseListCreate):
    serializer_class = TwitterTailoredAudienceSerializer
    contains_filter_include_pk = True
    list_filter_fields = ('tw_account_id', 'audience_type', )
    order_fields = ('tw_tailored_audience', '-tw_tailored_audience',
                    'tw_targeting_id', '-tw_targeting_id', 'last_update', '-last_update')

    
    def post(self, request, *args, **kwargs):
        csv_file = request.data.get('file')
        tw_account_id = request.data.get('tw_account_id')
        list_type = request.data.get('list_type')
        audience_name = request.data.get('audience_name')

        # save uploaded file on /tmp folder
        full_path = "/tmp/%s" % csv_file.name 
        fout = open(full_path, "wb+")
        for chunk in csv_file.chunks():
            fout.write(chunk)
        fout.close()
        
        # validate params
        if not csv_file or not tw_account_id or not list_type \
            or not audience_name:
            return Response(
                data=dict(msg="file or tw_account_id or list_type or" \
                    "audience_name is missing"), 
                status=status.HTTP_400_BAD_REQUEST)
            
        
        # check tw_account_id and make Client
        try:
            tw_account = TwitterAccount.objects.get(tw_account_id=tw_account_id)
            oauth_token = tw_account.tw_twitter_user_id.oauth_token \
                or settings.TW_ACCESS_TOKEN
            oauth_token_secret = tw_account.tw_twitter_user_id.oauth_secret \
                or settings.TW_ACCESS_SECRET
            _key = 'twitter_tailored_audiences_%s' % tw_account_id
            client = Client(
                    settings.TW_CONSUMER_KEY, 
                    settings.TW_CONSUMER_SECRET, oauth_token,
                    oauth_token_secret)
            tw_account_id = int_to_base36(int(tw_account_id))
        except Exception as e:
            return Response(data=dict(msg='invalid tw_account_id', 
                    detail=str(e)), status=status.HTTP_400_BAD_REQUEST)    
        
        error_details = ''
        error = False
        try:
            # TON upload
            input_file_path = TONUpload(client, full_path).perform()
            # remove query string
            input_file_path = urlparse.urljoin(input_file_path, urlparse.urlparse(input_file_path).path)          

            # Create a new placeholder audience with the POST accounts/:account_id/tailored_audiences endpoint.
            query_string = dict(
                name=audience_name,
                list_type=list_type
                )
            query_string = urllib.urlencode(query_string)

            resource = "/{api_version}/accounts/{account_id}/tailored_audiences?" \
                "{qs}".format(
                    api_version=settings.TW_API_VERSION, 
                    account_id=tw_account_id,
                    qs=query_string)
            response = Request(client, 'post', resource).perform()

            # if success
            if response.code == 200 or response.code == 201:
                tailored_audience_id = response.body['data'].get('id')
                query_string = dict(
                    tailored_audience_id=tailored_audience_id,
                    operation='ADD',
                    input_file_path=input_file_path
                )
                query_string = urllib.urlencode(query_string)

                # Change the audience by adding
                resource = "/{api_version}/accounts/{account_id}/" \
                "tailored_audience_changes?{query_string}".format(
                    api_version=settings.TW_API_VERSION,
                    account_id=tw_account_id,
                    query_string=query_string
                    )
                
                response = Request(client, 'post', resource).perform()
                redis_cache.delete(_key)
        except Error as e:
            error = True
            error_details = str(e)
        except Exception as e:
            error = True
            error_details = str(e)

        if error:
            return Response(
                data=dict(msg=error_details), 
                status=status.HTTP_400_BAD_REQUEST)

        return Response(data=dict(status='ok'))

    @property
    def queryset(self):
        request = self.request
        account_id = long(request.query_params.get('tw_account_id'))
        all = request.query_params.get('all')
        account = TwitterAccount.objects_raw.get(pk=account_id)
        oauth_token = account.tw_twitter_user_id.oauth_token
        oauth_secret = account.tw_twitter_user_id.oauth_secret
        _key = 'twitter_tailored_audiences_%s' % account_id

        # if not synced
        if not redis_cache.get(_key, False):
            res = TwitterTailoredAudience.fetch_tailored_audience(dict(account_id=account_id), True,
                                                                  oauth_token, oauth_secret)
            if res.get('success'):
                # timeout after 1 hour
                redis_cache.set(_key, 'synced', timeout=60*60)
        if all:
            return TwitterTailoredAudience.objects.order_by('-last_update').all()
        else:
            return TwitterTailoredAudience.objects.filter(targetable=1, audience_size__isnull=False).order_by('-last_update')
