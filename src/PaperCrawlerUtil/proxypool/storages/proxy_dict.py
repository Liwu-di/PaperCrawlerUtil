# -*- coding: utf-8 -*-
# @Time    : 2022/7/14 20:28
# @Author  : 银尘
# @FileName: proxy_dict.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
import random

from proxypool.exceptions import PoolEmptyException
from proxypool.schemas import Proxy
from proxypool.setting import PROXY_SCORE_MAX, PROXY_SCORE_MIN, PROXY_SCORE_INIT, NEED_LOG_REDIS
from random import choice
from typing import List
from loguru import logger
from proxypool.utils.proxy import is_valid_proxy, convert_proxy_or_proxies
from global_val import *
import global_val


class ProxyDict(object):
    """
    dict connection client of proxypool
    """

    def __init__(self, **kwargs):
        """
        init redis dict
        """
        self.dict = global_val.get_value("global_dict")

    def add(self, proxy: Proxy, score=PROXY_SCORE_INIT) -> int:
        """
        add proxy and set it to init score
        :param proxy: proxy, ip:port, like 8.8.8.8:88
        :param score: int score
        :return: result
        """
        if not is_valid_proxy(f'{proxy.host}:{proxy.port}'):
            if NEED_LOG_REDIS:
                logger.info(f'invalid proxy {proxy}, throw it')
            return
        if not self.exists(proxy):
            try:
                self.dict[proxy.string()] = score
                return 0
            except Exception as e:
                if NEED_LOG_REDIS:
                    logger.info("添加字典失败：{}".format(e))
                return -1

    def random(self) -> Proxy:
        """
        get random proxy
        firstly try to get proxy with max score
        if not exists, try to get proxy by rank
        if not exists, raise error
        :return: proxy, like 8.8.8.8:8
        """
        # try to get proxy with max score
        proxies = []
        for k in sorted(self.dict.items(), key=lambda kv: (kv[1], kv[0]), reverse=True):
            if k[1] == PROXY_SCORE_MAX:
                proxies.append(k[0])
        if len(proxies):
            return convert_proxy_or_proxies(choice(proxies))
        # else get proxy by rank
        proxies = []
        for k in sorted(self.dict.items(), key=lambda kv: (kv[1], kv[0]), reverse=True):
            if PROXY_SCORE_MIN <= k[1] <= PROXY_SCORE_MAX:
                proxies.append(k[0])
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
        self.dict[proxy.string()] = self.dict[proxy.string()] - 1
        score = self.dict[proxy.string()]
        if NEED_LOG_REDIS:
            logger.info(f'{proxy.string()} score decrease 1, current {score}')
        if score <= PROXY_SCORE_MIN:
            if NEED_LOG_REDIS:
                logger.info(f'{proxy.string()} current score {score}, remove')
            self.dict.pop(proxy.string())

    def exists(self, proxy: Proxy) -> bool:
        """
        if proxy exists
        :param proxy: proxy
        :return: if exists, bool
        """
        return proxy.string() in self.dict.keys()

    def max(self, proxy: Proxy) -> int:
        """
        set proxy to max score
        :param proxy: proxy
        :return: new score
        """
        if NEED_LOG_REDIS:
            logger.info(f'{proxy.string()} is valid, set to {PROXY_SCORE_MAX}')
        try:
            self.dict[proxy.string()] = PROXY_SCORE_MAX
            return 0
        except Exception as e:
            logger.info("更新字典分数失败：{}".format(e))
            return -1

    def count(self) -> int:
        """
        get count of proxies
        :return: count, int
        """
        return len(self.dict)

    def all(self) -> List[Proxy]:
        """
        get all proxies
        :return: list of proxies
        """
        proxy_list = []
        for item in self.dict.items():
            if PROXY_SCORE_MIN <= item[1] <= PROXY_SCORE_MAX:
                p = Proxy(item[0].split(":")[0], item[0].split(":")[1])
                proxy_list.append(p)
        return proxy_list

    def batch(self, cursor, count) -> List[Proxy]:
        """
        get batch of proxies
        :param cursor: scan cursor
        :param count: scan count
        :return: list of proxies
        """
        proxy_tuple_list = list(self.dict.items())
        res = []
        counts = 0
        if cursor >= len(proxy_tuple_list):
            cursor = 0
        for i in range(len(proxy_tuple_list)):
            flag = False
            if i >= cursor:
                flag = True
            if flag and counts < count:
                counts = counts + 1
                p = Proxy(proxy_tuple_list[i][0].split(":")[0], proxy_tuple_list[i][0].split(":")[1])
                res.append(p)
        return cursor + count, res


# if __name__ == '__main__':
#     conn = ProxyDict()
#     for k in range(100):
#         conn.add(Proxy(str(k), k))
#     print(conn.random())
#     print(conn.count())
#     print(conn.decrease(Proxy(0, 0)))
#     print(conn.all())
#     print(conn.max(Proxy(0, 0)))
#     print(conn.all())
#     print(conn.exists(Proxy(2, 2)))
#     c, ll = conn.batch(0, 10)
#     print(c, ll)
#     c, ll = conn.batch(c, 10)
#     print(c, ll)
#     print(conn.all())
