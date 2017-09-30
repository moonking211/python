from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.serializers.twitter.TwitterAccountSerializer import TwitterAccountSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class TwitterAccountDetail(BaseDetail):
    serializer_class = TwitterAccountSerializer

    @property
    def queryset(self):
        return TwitterAccount.objects.all()
