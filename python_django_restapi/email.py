from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template


def send_mail(mail_to, template, attrs=None, mail_from=None):
    if attrs is None:
        attrs = {}

    if mail_from is None:
        mail_from = settings.DEFAULT_FROM_EMAIL

    context = Context(attrs)
    subject = get_template("email.%s.subject.txt" % template).render(context)
    body = get_template("email.%s.body.html" % template).render(context)

    subject = subject.split("\n")[0]

    message = EmailMultiAlternatives(subject, body, mail_from, [mail_to])
    message.attach_alternative(body, "text/html")

    message.send()

def send_twitter_alert_email(attrs=None):
    if attrs is None:
        attrs = {}

    context = Context(attrs)
    subject = get_template("email.rate_limit_alert.subject.txt").render(context)
    body = get_template("email.rate_limit_alert.body.html").render(context)

    subject = subject.split("\n")[0]

    message = EmailMultiAlternatives(subject, body, settings.TW_RATE_LIMIT_EMAIL, [settings.TW_RATE_LIMIT_EMAIL])
    message.attach_alternative(body, "text/html")

    message.send()

def send_twitter_sync_error_email(attrs=None):
    if attrs is None:
        attrs = {}

    context = Context(attrs)
    subject = get_template("email.sync_error_alert.subject.txt").render(context)
    body = get_template("email.sync_error_alert.body.html").render(context)

    subject = subject.split("\n")[0]

    message = EmailMultiAlternatives(subject, body, settings.TW_SYNC_ERROR_EMAIL, [settings.TW_SYNC_ERROR_EMAIL])
    message.attach_alternative(body, "text/html")

    message.send()

def send_twitter_email(subject='', body='', email=settings.TW_SYNC_EMAIL):
    subject = subject
    body = body

    subject = subject.split("\n")[0]

    message = EmailMultiAlternatives(subject, body, email, [email])
    message.attach_alternative(body, "text/html")

    message.send()

def send_a9_scraper_error_email(attrs=None):
    if not settings.A9_SCRAPE_ERROR_ALERT:
        return
    if attrs is None:
        attrs = {}

    context = Context(attrs)
    subject = get_template("email.a9_scraper_error.subject.txt").render(context)
    body = get_template("email.a9_scraper_error.body.html").render(context)

    subject = subject.split("\n")[0]

    message = EmailMultiAlternatives(subject, body, settings.A9_SCRAPE_ERROR_EMAIL, [settings.A9_SCRAPE_ERROR_EMAIL])
    message.attach_alternative(body, "text/html")

    message.send()
