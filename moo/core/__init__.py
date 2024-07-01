# -*- coding: utf-8 -*-
"""
Core MOO functionality, object model, verbs.
"""

import logging

from .code import context

log = logging.getLogger(__name__)

def create_object(name,  *a, owner=None, location=None, parent=None, **kw):
    """
    [`TODO <https://gitlab.com/bubblehouse/django-moo/-/issues/11>`_]
    Creates and returns a new object whose parent is `parent` and whose owner is as described below.
    Either the given `parent` object must be None or a valid object with `derive` permission,
    or else the programmer must own parent or be a wizard; otherwise E_PERM is raised. E_PERM is
    also raised if owner is provided and not the same as the programmer, unless the programmer is a
    wizard. After the new object is created, its `initialize` verb, if any, is called with no arguments.

    The owner of the new object is either the programmer (if `owner` is not provided), the new object
    itself (if owner was given as None), or owner (otherwise).

    In addition, the new object inherits all of the other properties on `parent`. These properties have
    the same permission bits as on `parent`. If the `inherit` permission bit is set, then the owner of the
    property on the new object is the same as the owner of the new object itself; otherwise, the owner
    of the property on the new object is the same as that on parent.

    If the intended owner of the new object has a property named `ownership_quota` and the value of that
    property is an integer, then create_object() treats that value as a quota. If the quota is less than
    or equal to zero, then the quota is considered to be exhausted and create() raises E_QUOTA instead
    of creating an object. Otherwise, the quota is decremented and stored back into the `ownership_quota`
    property as a part of the creation of the new object.
    """
    if owner is None:
        owner =  context.get('caller')
    if location is None and owner:
        location = owner.location
    from .models.object import AccessibleObject
    return AccessibleObject.objects.create(
        name=name,
        location=location,
        owner=owner,
        parent=parent,
        *a, **kw
    )

def message_user(user_obj, message):
    """
    Send a asynchronous message to the user.

    :param user_obj: the Object of the User to message
    :param message: any pickle-able object
    """
    from .models.auth import Player
    try:
        player = Player.objects.get(avatar=user_obj)
    except Player.DoesNotExist:
        return
    from ..celery import app
    from kombu import Exchange, Queue
    with app.default_connection() as conn:
        channel = conn.channel()
        queue = Queue('messages', Exchange('moo', type='direct', channel=channel), f'user-{player.user.pk}', channel=channel)
        with app.producer_or_acquire() as producer:
            producer.publish(
                dict(message=message, caller=context.get('caller')),
                serializer='pickle',
                exchange=queue.exchange,
                routing_key=f'user-{player.user.pk}',
                declare=[queue],
                retry=True,
            )

class API:
    """
    This wrapper class makes it easy to use a number of contextvars.
    """
    class descriptor:
        """
        Used to perform dynamic lookups of contextvars.
        """
        def __init__(self, name):
            self.name = name

        def __get__(self, obj, objtype=None):
            d = context.vars.get({})
            return d.get(self.name)

        def __set__(self, obj, value):
            d = context.vars.get({})
            d[self.name] = value
            context.vars.set(d)

    caller = descriptor('caller')  # The user object that invoked this code
    writer = descriptor('writer')  # A callable that will print to the caller's console
    args = descriptor('args')
    kwargs = descriptor('kwargs')
    parser = descriptor('parser')

api = API()
