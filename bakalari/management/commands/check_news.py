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
from bakalari.newsfeed import Feed
from pybakalib.client import BakaClient

from bakalari.models import NotificationSubscription

import bleach

from pybakalib.errors import BakalariError


def notify(client, subscription, feed_item):
    {
        'pushbullet': notify_pushbullet,
        'email': notify_email,
    }.get(subscription.contact_type, notify_none)(client, subscription, feed_item)


def notify_none(client: BakaClient, subscription: NotificationSubscription, feed_item):
    print('Unknown contact type:', subscription.contact_type)


def notify_pushbullet(client: BakaClient, subscription: NotificationSubscription, feed_item):
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
    resp = requests.post('https://api.pushbullet.com/v2/pushes', headers=headers, data=json.dumps(body))
    resp.raise_for_status()


def notify_email(client: BakaClient, subscription: NotificationSubscription, feed_item):
    email = subscription.contact_id
    url = 'https://api.mailgun.net/v3/mg.bakaweb.tk/messages'
    unsubscribe_url = 'https://www.bakaweb.tk{}?unsubscribe=1&email={}'.format(str(reverse_lazy('register_email')), email)
    login_url = views.login_perm_create(subscription.url, subscription.perm_token)

    data = email_data.notification_email_data(email, subscription.name, feed_item, unsubscribe_url, None, login_url)

    resp = requests.post(url, data=data, auth=('api', 'key-a45d0a0f76d9e3dce37949cc0953e81b'))
    resp.raise_for_status()


logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Runs BakaNotifications check'

    def handle(self, *args, **options):
        print('[BAKANEWS CHECK STARTED]')
        subscriptions = NotificationSubscription.objects.all()
        for subscription in subscriptions:
            print('Checking news for {}'.format(subscription.name))
            try:
                client = BakaClient(subscription.url)
                client.login(subscription.perm_token)

                # Update saved details
                profile = client.get_module('login')
                if profile.name != subscription.name:
                    subscription.name = profile.name
                    subscription.save()

                # Check for news
                news = Feed(client)
                for n in news:
                    if n.date < subscription.last_check:
                        break
                    try:
                        notify(client, subscription, n)
                    except RequestException:
                        print('Failed to send notification...')
                subscription.last_check = datetime.now()
                subscription.save()
            except Exception:
                logger.exception('Failed...')

            logger.info('One second sleep...')
            time.sleep(1)
        print('[CHECK ENDED]')
