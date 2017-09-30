# encoding: utf-8
"""Defines JobStatus model."""

from __future__ import unicode_literals

from django.db import models
from django.utils import translation

TWITTER = 'twitter'
RTB = 'rtb'

JOB_TYPE = (
    ('twitter', translation.ugettext_lazy('Twitter')),
    ('rtb', translation.ugettext_lazy('RTB')),
)


class JobStatus(models.Model):
    """This model keeps finish time for cron jobs."""
    job_name = models.CharField(max_length=255, blank=False, null=False, primary_key=True)
    job_type = models.CharField(max_length=255, blank=False, null=False, choices=JOB_TYPE)
    last_finished = models.DateTimeField(blank=False, null=False)
    threshold = models.IntegerField(null=True)

    class Meta:
        db_table = 'job_status'
        app_label = 'restapi'
