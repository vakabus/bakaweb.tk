import json
from datetime import datetime
import time

import logging

import bakalari.email as email_data
import requests
from django.core.management import BaseCommand
from django.urls import reverse_lazy
from requests import RequestException

from bakalari import views
from bakalari.newsfeed import FeedItem
from pybakalib.client import BakaClient

from bakalari.models import NotificationSubscription

import bleach


def notify(subscription, feed_item):
    {
        'pushbullet': notify_pushbullet,
        'email': notify_email,
    }.get(subscription.contact_type, notify_none)(subscription, feed_item)


def notify_none(subscription: NotificationSubscription, feed_item):
    print('Unknown contact type:', subscription.contact_type)


def notify_pushbullet(subscription: NotificationSubscription, feed_item):
    api_key = subscription.contact_id
    body = {
        'type': 'note',
        'title': feed_item.title,
        'body': bleach.clean(feed_item.text.replace('<br>', '\n'), strip=True)
    }
    headers = {
        'Access-Token': api_key,
        'Content-Type': 'application/json'
    }
    resp = requests.post('https://api.pushbullet.com/v2/pushes', headers=headers, data=json.dumps(body))
    resp.raise_for_status()


def notify_email(subscription: NotificationSubscription, feed_item):
    email = subscription.contact_id
    url = 'https://api.mailgun.net/v3/mg.bakaweb.tk/messages'
    unsubscribe_url = 'https://www.bakaweb.tk{}?unsubscribe=1&email={}'.format(str(reverse_lazy('register_email')), email)
    login_url = views.login_perm_create(subscription.url, subscription.perm_token)

    data = email_data.notification_email_data(email, subscription.name, feed_item, unsubscribe_url, None, login_url)

    resp = requests.post(url, data=data, auth=('api', 'key-a45d0a0f76d9e3dce37949cc0953e81b'))
    resp.raise_for_status()


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ends subscription for the person with name provided in argument'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str)

    def handle(self, *args, **options):
        logger.info('Odstraňuji odběr pro {}'.format(options['name']))

        fi = FeedItem('Ukončení odběru zpráv z bakaweb.tk', 'Díky za používání služeb mého webu. Doufám, že to bylo k něčemu.</br></br>Hodně štěstí do dalších studií,</br>Vašek Šraier', None)

        subscriptions = NotificationSubscription.objects.filter(name=options['name'])
        for sub in subscriptions:
            notify(sub, fi)
            logger.info('\tOdstraněno - {}'.format(sub.contact_type))
            sub.delete()

        logger.info('Hotovo')