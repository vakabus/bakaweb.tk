import json
from datetime import datetime

import pytz
import requests
from django.core.management import BaseCommand
from requests import RequestException

from bakalari.newsfeed import Feed
from pybakalib.client import BakaClient

from bakalari.models import NotificationSubscription


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
        'body': feed_item.text
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
        print('Checking news for all subscribers...')
        subscriptions = NotificationSubscription.objects.all()
        for subscription in subscriptions:
            print('Checking news for ', subscription.name)
            client = BakaClient(subscription.url)
            client.login(subscription.perm_token)
            news = Feed(client)

            last_date = datetime.now()

            for n in news:
                if n.date < subscription.last_check:
                    break
                try:
                    last_date = n.date
                    notify(subscription, n)
                except RequestException:
                    break
            subscription.last_check = last_date
            subscription.save()
