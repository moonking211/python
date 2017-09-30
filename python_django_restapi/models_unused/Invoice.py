from django.db import models

from restapi.models_unused import Publisher


INVOICE_STATUS_CHOICES = (
    (-1, 'BelowMinPay'),
    (0, 'Created'),
    (1, 'Pending'),
    (2, 'Paid'),
    (3, 'Voided'),
    (4, 'Approved'),
)


class Invoice(models.Model):
    invoice_id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    publisher_id = models.ForeignKey(Publisher, db_column='publisher_id')
    credit = models.FloatField()
    debit = models.FloatField()
    method = models.CharField(max_length=255)
    notes = models.CharField(max_length=255, blank=True)
    status = models.IntegerField(choices=INVOICE_STATUS_CHOICES)
    type = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now=True)
    approver_id = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'invoice'
        app_label = 'restapi'

    def get_verbose_status(self):
        for choice in INVOICE_STATUS_CHOICES:
            if choice[0] == self.status:
                return choice[1]
        return self.status

    def __unicode__(self):
        return self.invoice_id
