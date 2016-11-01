import json
import traceback
from datetime import datetime

import pytz
import requests
from django.core.management import BaseCommand
from django.urls import reverse_lazy
from requests import RequestException

from bakalari.newsfeed import Feed
from pybakalib.client import BakaClient

from bakalari.models import NotificationSubscription

import bleach

from pybakalib.errors import BakalariError


def notify(subscription, feed_item):
    {
        'pushbullet': notify_pushbullet,
        'email': notify_email,
    }.get(subscription.contact_type, notify_none)(subscription, feed_item)


def notify_none(subscription, feed_item):
    print('Unknown contact type:', subscription.contact_type)


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
    resp = requests.post('https://api.pushbullet.com/v2/pushes', headers=headers, data=json.dumps(body))
    resp.raise_for_status()


def notify_email(subscription, feed_item):
    email = subscription.contact_id
    url = 'https://api.mailgun.net/v3/mg.bakaweb.tk/messages'
    unsubscribe_url = 'https://www.bakaweb.tk{}?unsubscribe=1&email={}'.format(str(reverse_lazy('register_email')),
                                                                               email)
    data = {
        'from': 'Bakaweb.tk <noreply@bakaweb.tk>',
        'to': email,
        'subject': '[BAKAWEB.TK] {}'.format(feed_item.title),
        'text': '{}\n\nOdhlašte se z těchto zpráv kliknutím na tento odkaz:\n{}'.format(
            bleach.clean(feed_item.text.replace('<br>', '\n')), unsubscribe_url),
        'html': '{}</br><hr></br>Tento email Vám byl doručen, protože jste přihlášeni k odběru novinek z Bakalářů přes server bakaweb.tk. Pro odhlášení klikňete <a href="{}">zde</a>.'.format(
            feed_item.text,
            unsubscribe_url)
    }
    resp = requests.post(url, data=data, auth=('api', 'key-a45d0a0f76d9e3dce37949cc0953e81b'))
    resp.raise_for_status()


class Command(BaseCommand):
    help = 'Runs BakaNotifications check'

    def handle(self, *args, **options):
        print('[BAKANEWS CHECK STARTED]')
        subscriptions = NotificationSubscription.objects.all()
        for subscription in subscriptions:
            try:
                print('Checking news for ', subscription.name)
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
                        notify(subscription, n)
                    except RequestException:
                        print('Failed to send notification...')
                subscription.last_check = datetime.now()
                subscription.save()
            except BakalariError as e:
                print('    Failed...')
                traceback.print_exc()
                print('')
        print('[CHECK ENDED]')
