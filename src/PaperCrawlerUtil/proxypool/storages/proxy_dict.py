# -*- coding: utf-8 -*-
# @Time    : 2022/7/14 20:28
# @Author  : 银尘
# @FileName: proxy_dict.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
import os
import pickle
import random

from PaperCrawlerUtil.proxypool.exceptions import PoolEmptyException
from PaperCrawlerUtil.proxypool.schemas import Proxy
from random import choice
from typing import List
from loguru import logger
from PaperCrawlerUtil.proxypool.utils.proxy import is_valid_proxy, convert_proxy_or_proxies
from PaperCrawlerUtil.global_val import *
import PaperCrawlerUtil.global_val as global_val
from PaperCrawlerUtil.constant import *


class ProxyDict(object):
    """
    dict connection client of proxypool
    """

    def __init__(self, **kwargs):
        """
        init redis dict
        """
        self.dict = global_val.get_value(CROSS_FILE_GLOBAL_DICT_CONF)
        self.need_storage_log = global_val.get_value(STORAGE_LOG_CONF)
        self.init_score = global_val.get_value(PROXY_SCORE_INIT)
        self.dict_path = global_val.get_value("dict_store_path")
        self.max_score = global_val.get_value(PROXY_SCORE_MAX)
        self.min_score = global_val.get_value(PROXY_SCORE_MIN)
        if len(self.dict_path) != 0 and os.path.isfile(self.dict_path) and os.path.getsize(self.dict_path) > 0:
            self.dict = self.load()

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
            try:
                self.dict[proxy.string()] = score
                return 0
            except Exception as e:
                if self.need_storage_log:
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
            if k[1] == self.max_score:
                proxies.append(k[0])
        if len(proxies):
            return convert_proxy_or_proxies(choice(proxies))
        # else get proxy by rank
        proxies = []
        for k in sorted(self.dict.items(), key=lambda kv: (kv[1], kv[0]), reverse=True):
            if self.min_score <= k[1] <= self.max_score:
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
        if self.need_storage_log:
            logger.info(f'{proxy.string()} score decrease 1, current {score}')
        if score <= self.min_score:
            if self.need_storage_log:
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
        if self.need_storage_log:
            logger.info(f'{proxy.string()} is valid, set to {self.max_score}')
        try:
            self.dict[proxy.string()] = self.max_score
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
            if self.min_score <= item[1] <= self.max_score:
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
        for i in range(len(proxy_tuple_list)):
            flag = False
            if i >= cursor:
                flag = True
            if flag and counts < count:
                counts = counts + 1
                p = Proxy(proxy_tuple_list[i][0].split(":")[0], proxy_tuple_list[i][0].split(":")[1])
                res.append(p)
        return cursor + counts, res

    def save(self) -> bool:
        try:
            with open(self.dict_path, mode="wb") as f:
                pickle.dump(self.dict, f, pickle.HIGHEST_PROTOCOL)
            f.close()
            return True
        except Exception as e:
            print("保存dict错误：{}".format(e))
            return False

    def load(self) -> dict:
        res = None
        try:
            with open(self.dict_path, mode="rb") as f:
                res = pickle.load(f)
            f.close()
            return res if (res is not None and len(res) != 0) else {}
        except Exception as e:
            print("加载字典错误：{}".format(e))
            return {}


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
