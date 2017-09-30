from restapi.models.twitter.TwitterUser import TwitterUser
from restapi.serializers.twitter.TwitterUserSerializer import TwitterUserSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class TwitterUserDetail(BaseDetail):
    serializer_class = TwitterUserSerializer

    @property
    def queryset(self):
        return TwitterUser.objects.all()
