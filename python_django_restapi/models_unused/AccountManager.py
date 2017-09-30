from django.db import models


class AccountManager(models.Model):
    account_manager_id = models.AutoField(primary_key=True)
    status = models.IntegerField(default=0, blank=True)
    # Commenting out the column below because we're using the legacy AppSponsor table
    # the img column is unreadable by Django which leads to an error when trying
    # to edit Account Managers.
    # When editing the Account Manager record in Admin, it checks to see if
    # the photo field is there because it's corrupt and cannot display the value of the column or
    # a upload photo image the post returns a 500 as the server doesn't know how to
    # handle the request.
    # By commenting out the line below, the model doesn't know about that column and
    # Django Admin will not populate the line on the admin panel.
    # Once we know appsponsor isn't using this table anymore, we should set this up so
    # that uploads via the admin panel are possible.
    # Note how we're generating the image url below, we should actually store the url and
    # return that value and then we can modify Django admin to store the image on an S3 and
    # just storing the corresponding url
    # photo_140x140 = models.ImageField(blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    title = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    phone_landline = models.CharField(max_length=15, blank=True)
    phone_mobile = models.CharField(max_length=15, blank=True)
    skype = models.CharField(max_length=50, blank=True)
    chat = models.CharField(max_length=50, blank=True)
    # photo_140x140 = models.BinaryField()

    def __unicode__(self):
        return self.first_name + " " + self.last_name

    def get_full_name(self):
        return self.__unicode__()

    def get_image_url(self):
        return '/static/home/img/{0}_{1}.png'.format(self.first_name, self.last_name).lower()

    class Meta:
        managed = True
        db_table = 'account_manager'
        app_label = 'restapi'
