from restapi.models.base import BaseModel
from restapi.models.managers import BaseManager
from django.db import models


class A9CookieManager(BaseManager):
    def own(self, queryset=None):
        return super(AdManager, self).own(queryset)

class A9Cookie(BaseModel):
    cookie_id = models.AutoField(primary_key=True)
    authenticity_token = models.CharField(max_length=255)
    cookie_text = models.TextField(blank=False)

    class Meta:
        db_table = 'a9_cookie'
        app_label = 'restapi'