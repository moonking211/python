from restapi.models.twitter.TwitterUser import TwitterUser
from restapi.serializers.twitter.TwitterUserSerializer import TwitterUserSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class TwitterUserList(BaseListCreate):
    serializer_class = TwitterUserSerializer
    contains_filter_include_pk = True
    query_filter_fields = ('name', )

    @property
    def queryset(self):
        return TwitterUser.objects.all().exclude(oauth_token='')
