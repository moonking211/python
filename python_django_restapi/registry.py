# encoding: utf-8

from __future__ import unicode_literals

from django.contrib.auth import signals

REGISTRY = {}


def on_user_logged_in(user, *unused_args, **unused_kwargs):
    """This function is used to update REGISTRY every time user is logged in.

    :param user: user that has logged id.
    :param unused_args: unused positional arguments.
    :param unused_kwargs: unused position keyword arguments.
    """
    REGISTRY['user'] = user


signals.user_logged_in.connect(on_user_logged_in)
