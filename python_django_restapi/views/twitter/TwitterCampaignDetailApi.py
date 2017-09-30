from django.conf import settings

from rest_framework.response import Response
from rest_framework import status

from restapi.models.twitter.TwitterCampaign import TwitterCampaign
from restapi.serializers.twitter.TwitterCampaignSerializer import TwitterCampaignSerializer
from restapi.views.base_view.BaseDetail import BaseDetail
from restapi.models.twitter.TwitterRevmap import TwitterRevmap

class TwitterCampaignDetail(BaseDetail):
    serializer_class = TwitterCampaignSerializer

    def update(self, request, *args, **kwargs):
        data = {}
        for f in request.DATA:
            data[f] = request.DATA[f]
        instance = self.get_object()
        data['account_id'] = instance.tw_account_id.tw_account_id
        if not data['run_contiuosly']:
            if data.get('start_time'):
                data['start_time'] = data['start_time'].replace('00:00.000Z', '00:00Z')
            if data.get('end_time'):
                data['end_time'] = data['end_time'].replace('00:00.000Z', '00:00Z')
        
        data['paused'] = data['status'] != 'enabled'
        res = TwitterCampaign.update(data)

        # update  CPI Target  for all Ad Groups under the External Campaign
        TwitterRevmap.objects.filter(tw_campaign_id=instance).update(opt_value=data['cpi_target_goal'])

        if res['success']:
            return Response(TwitterCampaignSerializer(self.get_object()).data)
        else:
            return Response(data=dict(message=res.get('message', ''), errors=res.get('errors', '')),
                            status=status.HTTP_400_BAD_REQUEST)
    @property
    def queryset(self):
        return TwitterCampaign.objects.all()
