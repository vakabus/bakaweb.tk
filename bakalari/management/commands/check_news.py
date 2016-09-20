import json
import traceback
from datetime import datetime

import pytz
import requests
from django.core.management import BaseCommand
from requests import RequestException

from bakalari.newsfeed import Feed
from pybakalib.client import BakaClient

from bakalari.models import NotificationSubscription

import bleach

from pybakalib.errors import BakalariError


def notify(subscription, feed_item):
    {
        'pushbullet': notify_pushbullet,
    }.get(subscription.contact_type, notify_none)(subscription, feed_item)


def notify_none(subscription, feed_item):
    print('Unknown contact type: ', subscription.contact_type)


def notify_pushbullet(subscription, feed_item):
    api_key = subscription.contact_id
    body = {
        'type': 'note',
        'title': feed_item.title,
        'body': bleach.clean(feed_item.text.replace('<br>', '\n'))
    }
    headers = {
        'Access-Token': api_key,
        'Content-Type': 'application/json'
    }
    resp = requests.post('https://api.pushbullet.com/v2/pushes',headers=headers, data=json.dumps(body))
    resp.raise_for_status()


class Command(BaseCommand):
    help = 'Runs BakaNotifications check'

    def handle(self, *args, **options):
        subscriptions = NotificationSubscription.objects.all()
        for subscription in subscriptions:
            try:
                print('Checking news for ', subscription.name)
                client = BakaClient(subscription.url)
                client.login(subscription.perm_token)
                news = Feed(client)

                for n in news:
                    if n.date < subscription.last_check:
                        break
                    try:
                        notify(subscription, n)
                    except RequestException:
                        print('Failed to send notification...')
                subscription.last_check = datetime.now()
                subscription.save()
            except BakalariError as e:
                print('    Failed...')
                traceback.print_exc()
                print('')
