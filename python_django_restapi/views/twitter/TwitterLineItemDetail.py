from django.conf import settings
from restapi.models.twitter.TwitterTargetingModels import TwitterTargeting
from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.serializers.twitter.TwitterLineItemSerializer import TwitterLineItemDetailSerializer, TwitterLineItem
from restapi.views.base_view.BaseDetail import BaseDetail
from rest_framework.response import Response
from rest_framework import status
from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
import copy
class TwitterLineItemDetail(BaseDetail):
    serializer_class = TwitterLineItemDetailSerializer

    @property
    def queryset(self):
        return TwitterLineItem.objects.all()

    def update(self, request, *args, **kwargs):
        line_item = self.get_object()
        data = copy.copy(request.data)
        data['account_id'] = line_item.tw_campaign_id.tw_account_id.tw_account_id
        data['campaign_id'] = line_item.tw_campaign_id.tw_campaign_id
        data['line_item_id'] = line_item.pk
        data['paused'] = data.get('status') != 'enabled'
        res = TwitterLineItem.update(data)
        if res['success']:
            res = TwitterTargeting.set_targeting(data['targeting'], data['account_id'])
            if not res['success']:
                return Response(dict(messages=res['error']['messages']), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(dict(error=res['message']), status=status.HTTP_400_BAD_REQUEST)
        data['tweet_ids'] = ','.join(data['tweet_ids'])
        res = TwitterPromotedTweet.set_promoted_tweet(data, data['account_id'])
        if res['success']:
            cpi_target_goal = data['cpi_target_goal']
            revmap, created = TwitterRevmap.objects_raw.get_or_create(campaign_id=line_item.tw_campaign_id.campaign_id,
                                                tw_campaign_id=line_item.tw_campaign_id.pk, tw_line_item_id=line_item.pk)
            revmap.opt_type = 'install'
            revmap.opt_value = cpi_target_goal
            revmap.save()
        else:
            return Response(dict(error='Associating promotable tweets with line item failed!'), status=status.HTTP_400_BAD_REQUEST)
        return Response(TwitterLineItemDetailSerializer(self.get_object()).data)

