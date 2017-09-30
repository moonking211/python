from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.serializers.twitter.TwitterRevmapSerializer import TwitterRevmapSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class TwitterRevmapList(BaseListCreate):
    serializer_class = TwitterRevmapSerializer

    @property
    def queryset(self):
        return TwitterRevmap.objects.all()
