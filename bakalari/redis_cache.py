import logging

import redis

from pybakalib.client import ResponseCache

logger = logging.getLogger(__name__)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RedisCache(ResponseCache, metaclass=Singleton):
    def __init__(self):
        self._connection = redis.StrictRedis()
        self._connection.ping()

    def store(self, url: str, token: str, module: str, data: str):
        try:
            self._connection.setex("{}{}{}".format(url, token, module), 10*60, data.encode('utf8'))
        except ConnectionError:
            logger.exception("Can't connect to Redis...")

    def get(self, url: str, token: str, module: str):
        try:
            result = self._connection.get("{}{}{}".format(url, token, module))
            if result is None:
                return None
            return result.decode('utf8')
        except ConnectionError:
            logger.exception("Can't connect to Redis...")
            return None
