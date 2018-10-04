import json
from datetime import datetime
import time

import logging

import bakalari.email as email_data
import requests
from django.core.management import BaseCommand
from django.urls import reverse_lazy
from requests import RequestException

from bakalari.newsfeed import Feed
from bakalari.redis_cache import RedisCache
from pybakalib.client import BakaClient

from bakalari.models import NotificationSubscription, Session

import bleach


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
        'body': bleach.clean(feed_item.text.replace('<br>', '\n'), strip=True)
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
    user = Session(url=subscription.url, perm_token=subscription.perm_token)
    login_url = user.get_login_link()

    data = email_data.notification_email_data(email, subscription.name, feed_item, unsubscribe_url, None, login_url)

    resp = requests.post(url, data=data, auth=('api', 'key-a45d0a0f76d9e3dce37949cc0953e81b'))
    resp.raise_for_status()


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Runs BakaNotifications check'

    def handle(self, *args, **options):
        logger.info('[BAKANEWS CHECK STARTED]')
        logger.error("Somethings seriously wrong. The check is forcefully disabled.")
        return


        subscriptions = NotificationSubscription.objects.order_by('last_check')
        for subscription in subscriptions:
            # Service termination check
            if subscription.failed_checks > 9648:  # approx 65 days
                if subscription.contact_type == 'email':
                    resp = requests.post(
                        'https://api.mailgun.net/v3/mg.bakaweb.tk/messages',
                        data={
                            'from': 'Bakaweb.tk <noreply@bakaweb.tk>',
                            'to': subscription.contact_id,
                            'subject': '[BAKAWEB.TK] Přerušení odběru novinek',
                            'text': email_data.termination_message(subscription)
                        },
                        auth=('api', 'key-a45d0a0f76d9e3dce37949cc0953e81b')
                    )
                    resp.raise_for_status()
                elif subscription.contact_type == 'pushbullet':
                    body = {
                        'type': 'note',
                        'title': "[BAKAWEB.TK] Přerušení odběru novinek",
                        'body': email_data.termination_message(subscription)
                    }
                    headers = {
                        'Access-Token': subscription.contact_id,
                        'Content-Type': 'application/json'
                    }
                    resp = requests.post('https://api.pushbullet.com/v2/pushes', headers=headers, data=json.dumps(body))
                    resp.raise_for_status()
                print("Notification subscription terminated for {}".format(subscription.name))
                subscription.delete()
                continue

            logger.info('Checking news for {}'.format(subscription.name))
            try:
                client = BakaClient(subscription.url, cache=RedisCache())
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
                        logger.info("Sending notification...")
                        notify(client, subscription, n)
                    except RequestException:
                        logger.info('Failed to send notification...')

                # We need to store the latest time the server reports, not server local time to prevent issues caused by different time configurations
                subscription.last_check = max(map(lambda n: n.date, news)) if len(news) > 0 else datetime.now()
                subscription.failed_checks = 0
                subscription.save()
            except Exception:
                logger.exception('Failed...')
                subscription.failed_checks += 1
                subscription.save()

            logger.info('One second sleep...')
            time.sleep(1)
        logger.info('[CHECK ENDED]')
