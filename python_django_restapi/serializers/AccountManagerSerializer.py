from rest_framework import serializers
from restapi.models.AccountManager import AccountManager
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.EmailField import EmailField


class AccountManagerSerializer(BaseModelSerializer):
    first_name = serializers.CharField(max_length=50, required=True)
    last_name = serializers.CharField(max_length=50, required=True)
    title = serializers.CharField(max_length=50, required=True)
    email = EmailField(max_length=50, required=True)

    # pylint: disable=old-style-class
    class Meta:
        model = AccountManager
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=AccountManager.objects_raw.all(),
                fields=('email', 'first_name', 'last_name', 'title')
            )
        ]
