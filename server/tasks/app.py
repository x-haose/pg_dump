from __future__ import absolute_import, unicode_literals

from celery import Celery


app = Celery(
    "proj",
    broker="amqp://admin:adminadmin5200.@rabbit:5672//",
    include=["server.tasks"],
)
