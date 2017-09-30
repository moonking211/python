from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.serializers.twitter.TwitterLineItemSerializer import TwitterLineItemSerializer
from rest_framework import generics, permissions
from rest_framework.response import Response


class TwitterLineItemBulk(generics.CreateAPIView):
    serializer_class = TwitterLineItemSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        tw_line_items = request.DATA.get('tw_line_items')
        success_count = 0
        for obj in tw_line_items:
            if obj.get('tw_line_item_id'):
                tw_line_item_id = obj['tw_line_item_id']
                instance = TwitterLineItem.objects.filter(tw_line_item_id=tw_line_item_id).first()


                if obj.get('bid_amount_local_micro') and \
                                instance.bid_amount_local_micro != obj['bid_amount_local_micro']:
                    account_id = instance.tw_campaign_id.tw_account_id.tw_account_id
                    data = dict(account_id=account_id, line_item_id=tw_line_item_id, bid_amount_local_micro=obj.get('bid_amount_local_micro'), paused=(instance.status!='enabled'))
                    res = TwitterLineItem.update(data)
                    if res['success']:
                        success_count += 1

                tw_campaign_id = instance.tw_campaign_id.tw_campaign_id
                campaign = instance.tw_campaign_id.campaign_id

                if obj.get('cpi_target_goal'):
                    revmap, created = TwitterRevmap.objects.get_or_create(campaign_id=campaign,
                                                                          tw_campaign_id=tw_campaign_id,
                                                                          tw_line_item_id=tw_line_item_id)
                    revmap.opt_type = 'install'
                    if revmap.opt_value != obj['cpi_target_goal']:
                        revmap.opt_value = obj['cpi_target_goal']
                    revmap.save()

        return Response({'status': 'ok', 'success_count': success_count})