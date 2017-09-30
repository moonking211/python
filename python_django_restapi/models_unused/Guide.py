from django.core.urlresolvers import reverse
from django.db import models


class Guide(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.CharField(max_length=50, default=None, blank=True, null=True)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        import re
        return reverse('dashboard:guide-detail', args=[re.sub(r'\w+', '_', self.title).lower()])

    class Meta:
        managed = True
        db_table = 'guide'
        app_label = 'restapi'
