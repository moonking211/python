from django.conf import settings

from restapi.models.twitter.TwitterAppCard import TwitterAppCard
from restapi.serializers.twitter.TwitterAppCardSerializer import TwitterAppCardSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class TwitterAppCardDetail(BaseDetail):
    serializer_class = TwitterAppCardSerializer

    @property
    def queryset(self):
        return TwitterAppCard.objects.all()
