from django.conf import settings
from django.utils.http import int_to_base36
from django.core.cache import cache as redis_cache

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from restapi.models.twitter.TwitterTailoredAudience import TwitterTailoredAudience
from restapi.serializers.twitter.TwitterTailoredAudienceSerializer import TwitterTailoredAudienceSerializer
from restapi.views.base_view.BaseDetail import BaseDetail

from twitter_ads.client import Client
from twitter_ads.http import Request
from twitter_ads.error import Error


class TwitterTailoredAudienceDetail(BaseDetail):
    serializer_class = TwitterTailoredAudienceSerializer

    def delete(self, request, *args, **kwargs):
		instance = self.get_object()
		try:
			tw_account = instance.tw_account_id    
			account_id = tw_account.pk
			oauth_token = tw_account.tw_twitter_user_id.oauth_token \
				or settings.TW_ACCESS_TOKEN
			oauth_token_secret = tw_account.tw_twitter_user_id.oauth_secret \
				or settings.TW_ACCESS_SECRET
			_key = 'twitter_tailored_audiences_%s' % account_id
			client = Client(
					settings.TW_CONSUMER_KEY, 
					settings.TW_CONSUMER_SECRET, oauth_token,
					oauth_token_secret)
			tw_account_id = int_to_base36(int(tw_account.pk))
			audience_id = int_to_base36(instance.pk)
		except Exception as e:
			return Response(data=dict(msg='invalid tw_account_id', 
					detail=str(e)), status=status.HTTP_400_BAD_REQUEST)  
		
		try:
			resource = "/{api_version}/accounts/{account_id}/" \
				"tailored_audiences/{audience_id}".format(
					api_version=settings.TW_API_VERSION, 
					account_id=tw_account_id,
					audience_id=audience_id)
			response = Request(client, 'delete', resource).perform()
		except Error as e:
			return Response(
				data=dict(msg=str(e)), 
				status=status.HTTP_400_BAD_REQUEST)
		
		instance.delete()
		redis_cache.delete(_key)

		return Response(data=dict(status='ok'))

    @property
    def queryset(self):
        return TwitterTailoredAudience.objects.all()
