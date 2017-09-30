from django.db import models


class Announcement(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField(blank=True, null=True)
    expiration = models.DateField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    subject = models.CharField(max_length=140)
    body = models.TextField(blank=True)
    class Meta:
        managed = True
        db_table = 'announcement'
        app_label = 'restapi'

    def __unicode__(self):
        return self.subject

    def get_serializable(self):
        date_str = None
        if self.date != None:
            date_str = self.date.strftime('%b %d, %Y')
        return {'subject': self.subject, 'body': self.body, 'date': date_str}
