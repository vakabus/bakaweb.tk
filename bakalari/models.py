import base64
import urllib
from datetime import datetime

from django.contrib.sessions.backends.base import SessionBase
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.db import models

from bakalari.crypto import encrypt, decrypt
from bakalari.redis_cache import RedisCache
from pybakalib.client import BakaClient
from pybakalib.errors import BakalariError, LoginError


class NotificationSubscription(models.Model):
    url = models.CharField(max_length=128)
    name = models.CharField(max_length=32)
    perm_token = models.CharField(max_length=128)
    last_check = models.DateTimeField()
    contact_type = models.CharField(max_length=16)
    contact_id = models.CharField(max_length=128)
    failed_checks = models.IntegerField(default=0)

    def __str__(self):
        return '{} (last check: {})'.format(self.name, self.last_check.strftime('%d.%m. %H:%M:%S'))


class LogUser2(models.Model):
    user_id = models.CharField(max_length=128)
    school = models.CharField(max_length=256)
    dashboard_count = models.PositiveSmallIntegerField(default=0)
    subject_count = models.PositiveSmallIntegerField(default=0)
    last_seen = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return '{}... ({} dashboards)'.format(self.user_id[:8], str(self.dashboard_count))

    @staticmethod
    def get_user_id(username, password):
        id = username + password
        hasher = PBKDF2PasswordHasher()
        hash = hasher.encode(id, "bakasalt", 100000)
        return hash.strip()


class LogSubject2(models.Model):
    subject = models.CharField(max_length=64)
    count = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return '{}: {}'.format(self.subject, str(self.count))


class Session(SessionBase):
    def __init__(self, url=None, username=None, password=None, perm_token=None):
        self.username = username
        self.password = password
        self.real_name = None
        self.school_name = None
        self.token = perm_token
        self.url = url

        self.logged_in = False

    def login(self):
        client = self.get_baka_client()
        try:
            if self.token is None:
                client.login(self.username, self.password)
            else:
                client.login(self.token)
                self.username = self.token[7:self.token.find('*', 7)]

            account = client.get_module('login')
            self.real_name = account.name
            self.school_name = account.school
            self.token = client.token_perm
            self.logged_in = True
        except (BakalariError, LoginError):
            pass

    def get_login_link(self) -> str:
        def prep(s):
            return s.replace('|', "?%")

        s = "{}|{}".format(prep(self.url), prep(self.token))
        return 'https://www.bakaweb.tk/login/?d=' + urllib.parse.quote(encrypt(s))

    @staticmethod
    def login_by_link(b64: str) -> 'Session':
        try:
            s = decrypt(b64)
            url, token = s.replace('?%', '|').split('|')
            obj = Session(url=url, perm_token=token)
            obj.login()
            return obj
        except:
            return Session()

    def is_logged_in(self) -> bool:
        return self.logged_in

    def get_baka_client(self) -> BakaClient:
        url = self.url.replace('bakaweb.tk', 'bakalari.ceskolipska.cz')
        client = BakaClient(url, cache=RedisCache())
        if self.token is not None:
            client.login(self.token)
        return client

    def get_subject_averages(self):
        if not self.is_logged_in():
            return None

        client = self.get_baka_client()
        weights = client.get_module('predvidac')
        marks = client.get_module('znamky')
        return marks.get_all_averages(weights)
