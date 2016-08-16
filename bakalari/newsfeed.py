import urllib

import bleach as bleach
from django.contrib.syndication import views
from django.core.urlresolvers import reverse
from pybakalib.client import BakaClient


class Feed(list):
    def __init__(self, client):
        super(Feed, self).__init__()
        messages = client.get_module('prijate')
        noticeboard = client.get_module('nastenka')
        marks = client.get_module('znamky')

        for message in messages:
            self.append(FeedItem(
                ''.join(('Zpráva od ', message.sender)),
                bleach.clean('\n'.join((x for x in (message.title, message.text) if x is not None)),
                             tags=['b', 'u', 'i', 'a', 'br']),
                message.date
            ))
        for notice in noticeboard:
            self.append(FeedItem(
                ''.join(('Zpráva od ', notice.sender)),
                bleach.clean('\n'.join((x for x in (notice.title, notice.text) if x is not None)),
                             tags=['b', 'u', 'i', 'a', 'br']),
                notice.date
            ))
        for subj in marks:
            for mark in subj.get_marks():
                self.append(FeedItem(
                    ''.join((subj.abbreviation, ' - ', mark.mark)),
                    ', '.join((x for x in (mark.caption, mark.description) if x is not None)),
                    mark.date
                ))
        self.sort(key=lambda x: x.date, reverse=True)

        self.link = client.url


class FeedItem(object):
    def __init__(self, title, text, date):
        self.title = title
        self.text = text
        self.date = date


class RSSFeed(views.Feed):
    title = 'Novinky z Bakalářů'
    description = 'Nové známky a zprávy...'

    def get_object(self, request, *args, **kwargs):
        client = BakaClient(request.GET['url'])
        client.login(request.GET['token'])
        return Feed(client)

    def items(self, obj):
        return obj[:30]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.text

    def item_link(self, item):
        return reverse('index')

    def link(self, obj):
        return obj.link