from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.serializers.twitter.TwitterRevmapSerializer import TwitterRevmapSerializer
from restapi.views.base_view.BaseDetail import BaseDetail
from django.shortcuts import get_object_or_404


class TwitterRevmapDetail(BaseDetail):
    # Retrieve, update or delete a revmap instance.
#    queryset = Revmap.objects.all()
    serializer_class = TwitterRevmapSerializer

    def get_object(self):
        return get_object_or_404(TwitterRevmap, campaign_id=self.kwargs['campaign_id'])

    @property
    def queryset(self):
        return TwitterRevmap.objects.all()
