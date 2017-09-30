from restapi.models.twitter.TwitterAppCard import TwitterAppCard
from restapi.serializers.twitter.TwitterAppCardSerializer import TwitterAppCardSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class TwitterAppCardList(BaseListCreate):
    serializer_class = TwitterAppCardSerializer
    contains_filter_include_pk = True
    query_filter_fields = ('tw_app_card', 'tw_app_card_id')
    order_fields = ('tw_app_card', '-tw_app_card',
                    'tw_app_card_id', '-tw_app_card_id')

    @property
    def queryset(self):
        return TwitterAppCard.objects.all()
