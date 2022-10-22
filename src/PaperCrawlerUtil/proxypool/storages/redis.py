import redis

import PaperCrawlerUtil.global_val as global_val
from PaperCrawlerUtil.proxypool.exceptions import PoolEmptyException
from PaperCrawlerUtil.proxypool.schemas import Proxy
from random import choice
from typing import List
from loguru import logger
from PaperCrawlerUtil.proxypool.utils.proxy import is_valid_proxy, convert_proxy_or_proxies
from PaperCrawlerUtil.constant import *


REDIS_CLIENT_VERSION = redis.__version__
IS_REDIS_VERSION_2 = REDIS_CLIENT_VERSION.startswith('2.')


class RedisClient(object):
    """
    @todo: 这里看能不能加一个全局数组的形式，redis还得本地启动或者有服务器，麻烦，或者写文件也可以
    redis connection client of proxypool
    """

    def __init__(self, host="127.0.0.1", port=6379, password="", db=0, connection_string="", **kwargs):
        """
        init redis client
        :param host: redis host
        :param port: redis port
        :param password: redis password
        :param connection_string: redis connection_string
        """
        # if set connection_string, just use it
        if len(connection_string) > 0:
            self.db = redis.StrictRedis.from_url(connection_string, decode_responses=True, **kwargs)
        else:
            self.db = redis.StrictRedis(
                host=host, port=port, password=password, db=db, decode_responses=True, **kwargs)
        self.need_storage_log = global_val.get_value(STORAGE_LOG_CONF)
        self.init_score = global_val.get_value(PROXY_SCORE_INIT)
        self.max_score = global_val.get_value(PROXY_SCORE_MAX)
        self.min_score = global_val.get_value(PROXY_SCORE_MIN)
        self.redis_key = global_val.get_value(REDIS_CONF)[4]

    def add(self, proxy: Proxy) -> int:
        """
        add proxy and set it to init score
        :param proxy: proxy, ip:port, like 8.8.8.8:88
        :param score: int score
        :return: result
        """
        score = self.init_score
        if not is_valid_proxy(f'{proxy.host}:{proxy.port}'):
            if self.need_storage_log:
                logger.info(f'invalid proxy {proxy}, throw it')
            return
        if not self.exists(proxy):
            if IS_REDIS_VERSION_2:
                return self.db.zadd(self.redis_key, score, proxy.string())
            return self.db.zadd(self.redis_key, {proxy.string(): score})

    def random(self) -> Proxy:
        """
        get random proxy
        firstly try to get proxy with max score
        if not exists, try to get proxy by rank
        if not exists, raise error
        :return: proxy, like 8.8.8.8:8
        """
        # try to get proxy with max score
        proxies = self.db.zrangebyscore(
            self.redis_key, self.max_score, self.max_score)
        if len(proxies):
            return convert_proxy_or_proxies(choice(proxies))
        # else get proxy by rank
        proxies = self.db.zrevrange(
            self.redis_key, self.min_score, self.max_score)
        if len(proxies):
            return convert_proxy_or_proxies(choice(proxies))
        # else raise error
        raise PoolEmptyException

    def decrease(self, proxy: Proxy) -> int:
        """
        decrease score of proxy, if small than PROXY_SCORE_MIN, delete it
        :param proxy: proxy
        :return: new score
        """
        if IS_REDIS_VERSION_2:
            self.db.zincrby(self.redis_key, proxy.string(), -1)
        else:
            self.db.zincrby(self.redis_key, -1, proxy.string())
        score = self.db.zscore(self.redis_key, proxy.string())
        if self.need_storage_log:
            logger.info(f'{proxy.string()} score decrease 1, current {score}')
        if score <= self.min_score:
            if self.need_storage_log:
                logger.info(f'{proxy.string()} current score {score}, remove')
            self.db.zrem(self.redis_key, proxy.string())

    def exists(self, proxy: Proxy) -> bool:
        """
        if proxy exists
        :param proxy: proxy
        :return: if exists, bool
        """
        return not self.db.zscore(self.redis_key, proxy.string()) is None

    def max(self, proxy: Proxy) -> int:
        """
        set proxy to max score
        :param proxy: proxy
        :return: new score
        """
        if self.need_storage_log:
            logger.info(f'{proxy.string()} is valid, set to {self.max_score}')
        if IS_REDIS_VERSION_2:
            return self.db.zadd(self.redis_key, self.max_score, proxy.string())
        return self.db.zadd(self.redis_key, {proxy.string(): self.max_score})

    def count(self) -> int:
        """
        get count of proxies
        :return: count, int
        """
        return self.db.zcard(self.redis_key)

    def all(self) -> List[Proxy]:
        """
        get all proxies
        :return: list of proxies
        """
        return convert_proxy_or_proxies(self.db.zrangebyscore(self.redis_key, self.min_score, self.max_score))

    def batch(self, cursor, count) -> List[Proxy]:
        """
        get batch of proxies
        :param cursor: scan cursor
        :param count: scan count
        :return: list of proxies
        """
        cursor, proxies = self.db.zscan(self.redis_key, cursor, count=count)
        return cursor, convert_proxy_or_proxies([i[0] for i in proxies])

    @staticmethod
    def save() -> bool:
        print("redis方式不需要保存")

    @staticmethod
    def load() -> dict:
        print("redis方式不需要加载")


if __name__ == '__main__':
    conn = RedisClient()
    result = conn.random()
    print(result)
