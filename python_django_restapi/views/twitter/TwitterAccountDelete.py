from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.serializers.twitter.TwitterAccountSerializer import TwitterAccountSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated


class TwitterAccountDelete(generics.DestroyAPIView):
    serializer_class = TwitterAccountSerializer
    permission_classes = (IsAuthenticated, )

    @property
    def queryset(self):
        return TwitterAccount.objects_raw.all()