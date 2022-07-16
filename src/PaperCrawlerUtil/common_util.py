import sys
from typing import List, Optional, Callable, Any, Iterable, Mapping

import global_val
from storages.proxy_dict import ProxyDict

sys.path.append("PaperCrawlerUtil")
sys.path.append("PaperCrawlerUtil/proxypool")
sys.path.append("PaperCrawlerUtil/proxypool/*")
sys.path.append("proxypool/crawlers/public/*")
sys.path.append("proxypool/crawlers/private/*")
sys.path.append("proxypool/crawlers/*")
sys.path.append("proxypool/exceptions/*")
sys.path.append("proxypool/processors/*")
sys.path.append("proxypool/schemas/*")
sys.path.append("proxypool/storages/*")
sys.path.append("proxypool/utils/*")
sys.path.append("proxypool/*")
import logging
import os
import random
import threading
import time
import requests
from proxypool.setting import *
from requests.cookies import RequestsCookieJar
from proxypool.processors.getter import Getter
from proxypool.processors.server import app
from proxypool.processors.tester import Tester
from global_val import *
from constant import *


PROXY_POOL_URL = ""
logging.basicConfig(filename='crawler_util.log', level=logging.WARNING)
log_style = LOG_STYLE_PRINT

PROXY_POOL_CAN_RUN_FLAG = True


def log(string: str) -> None:
    global log_style
    if log_style == LOG_STYLE_LOG:
        logging.warning(string)
    elif log_style == LOG_STYLE_PRINT:
        print(string)
    elif log_style == LOG_STYLE_ALL:
        logging.warning(string)
        print(string)


class CanStopThread(threading.Thread):

    def __init__(self) -> None:
        super().__init__()

    def stop(self):
        raise ThreadStopException()


class ThreadGetter(CanStopThread):
    def __init__(self, redis_host, redis_port, redis_password, redis_database, storage, need_log: bool = True):
        threading.Thread.__init__(self)
        self.need_log = need_log
        self.host = redis_host
        self.port = redis_port
        self.password = redis_password
        self.database = redis_database
        self.storage = storage

    def run(self):
        log("启动getter")
        Getter(redis_host=self.host, redis_port=self.port,
               redis_password=self.password, redis_database=self.database,
               need_log=self.need_log, storage=self.storage).run()

    def save_dict(self):
        if self.storage == "redis":
            return True
        else:
            log("保存dict")
            d = ProxyDict()
            d.save()


class ThreadTester(CanStopThread):
    def __init__(self, redis_host, redis_port, redis_password, redis_database, storage, need_log: bool = True):
        threading.Thread.__init__(self)
        self.need_log = need_log
        self.host = redis_host
        self.port = redis_port
        self.password = redis_password
        self.database = redis_database
        self.storage = storage

    def run(self):
        log("启动tester")
        Tester(redis_host=self.host, redis_port=self.port,
               redis_password=self.password, redis_database=self.database,
               need_log=self.need_log, storage=self.storage).run()

    def save_dict(self):
        if self.storage == "redis":
            return True
        else:
            log("保存dict")
            d = ProxyDict()
            d.save()


class ThreadServer(CanStopThread):
    def __init__(self, host, port, threaded):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.threaded = threaded

    def run(self):
        log("启动server")
        app.run(host=self.host, port=self.port, threaded=self.threaded, use_reloader=False)

    def save_dict(self):
        if global_val.get_value("storage") == "redis":
            return True
        else:
            log("保存dict")
            d = ProxyDict()
            d.save()


def set_cross_file_variable(key_val: List[tuple]) -> bool:
    """
    设置全局跨文件变量，根据给出的tuple列表
    :param key_val: 列表，其中元素为tuple，第一个元素为key，第二为value
    :return:
    """
    if type(key_val) != list:
        log("全局变量设置错误，请提供List类型并且保证所有元素都是tuple")
        return False
    for k_v in key_val:
        if type(k_v) != tuple:
            log("全局变量设置错误，请提供List类型并且保证所有元素都是tuple")
            return False
    global_val._init()
    for k_v in key_val:
        try:
            global_val.set_value(k_v[0], k_v[1])
        except Exception as e:
            log("设置全局跨文件变量{}错误：{}".format(k_v, e))
            return False
    return True


def is_ip(proxy_test: str = "") -> bool:
    """
    测试字符串是否是一个ip地址
    :param proxy_test: 待测试字符串
    :return:是则返回True
    """
    flag = False
    if type(proxy_test) != str:
        log("参数{}不是字符串".format(proxy_test))
        return False
    if len(proxy_test) == 0:
        return flag
    for i in list(proxy_test):
        if i != ":" and i != "." and not i.isdigit() and i != "h" and i != "h" and (
                i != "t") and i != "p" and i != "s" and i != "/":
            flag = False
            break
        if i == list(proxy_test)[len(proxy_test) - 1]:
            flag = True
    return flag


def stop_thread(thread_list: List[CanStopThread] = []) -> int:
    count = 0
    for t in thread_list:
        try:
            t.stop()
        except ThreadStopException as e:
            log("线程{}结束".format(t.name))
            count = count + 1
        except Exception as e:
            log("结束线程{}错误{}".format(t.name, e))
    return count


def basic_config(log_file_name: str = "crawler_util.log",
                 log_level=logging.WARNING,
                 proxy_pool_url: str = "",
                 logs_style: str = LOG_STYLE_PRINT,
                 require_proxy_pool: bool = False,
                 redis_host: str = "127.0.0.1",
                 redis_port: int = 6379,
                 redis_database: int = 0,
                 redis_password: str = "",
                 need_getter_log: bool = True,
                 need_tester_log: bool = True,
                 need_storage_log: bool = True,
                 api_host: str = "127.0.0.1",
                 api_port: int = 5555,
                 proxypool_storage: str = "redis",
                 set_daemon: bool = True,
                 proxy_score_max: int = 100,
                 proxy_score_min: int = 0,
                 proxy_score_init: int = 10,
                 proxy_number_max: int = 50000,
                 proxy_number_min: int = 0) -> tuple:
                 dict_store_path: str = "dict.db",
                 set_daemon: bool = True) -> tuple:
    """
    :param dict_store_path: 选择字典方式存储时，最后文件保存的地址（同时也是加载地址）
    :param proxy_number_min: 最小池容量
    :param proxy_number_max: 最大池容量
    :param proxy_score_init: proxy评分的初始值，添加的时候自动赋值为该值
    :param proxy_score_min: proxy评分的最小值，小于此值时，丢弃
    :param proxy_score_max: proxy评分的最大值，测试可用时，赋值为该值
    :param set_daemon: 设置是否需要守护线程，即主线程结束，子线程也结束
    :param need_storage_log: 是否需要存储模块（redis)等的日志信息（不影响重要信息输出）
    :param proxypool_storage:代理池的存储方式，可以选择redis或者dict
    :param api_port: FLASK端口
    :param api_host: FLASK地址
    :param redis_password: redis 密码
    :param need_tester_log: 是否需要测试代理模块的日志信息（不影响重要信息输出）
    :param need_getter_log: 是否需要获取代理模块的日志信息（不影响重要信息输出）
    :param redis_database: redis数据库
    :param redis_port: redis端口号
    :param redis_host: redis主机ip
    :param require_proxy_pool: 是否需要启用proxy_pool项目获取代理连接
    :param log_file_name: 日志文件名称
    :param log_level: 日志等级
    :param proxy_pool_url: 代理获取地址
    :param logs_style: log表示使用日志文件，print表示使用控制台，all表示两者都使用
    :return:
    """
    global PROXY_POOL_URL, PROXY_POOL_CAN_RUN_FLAG
    global log_style
    set_cross_file_variable([(REDIS_CONF, (redis_host, redis_port, redis_password, redis_database)),
                             (STORAGE_CONF, proxypool_storage), (CROSS_FILE_GLOBAL_DICT_CONF, {}),
                             (STORAGE_LOG_CONF, need_storage_log), (GETTER_LOG_CONF, need_getter_log),
                             (TESTER_LOG_CONF, need_tester_log), (PROXY_SCORE_MAX, proxy_score_max),
                             (PROXY_SCORE_MIN, proxy_score_min), (PROXY_SCORE_INIT, proxy_score_init),
                             (POOL_MAX, proxy_number_max), (POOL_MIN, proxy_number_min), ("dict_store_path", dict_store_path)])
    PROXY_POOL_URL = proxy_pool_url
    log_style = logs_style
    if require_proxy_pool and PROXY_POOL_CAN_RUN_FLAG and len(
            redis_host) > 0 and 0 <= redis_database <= 65535 and (
            0 <= redis_port <= 65535) and len(api_host) > 0 and (65535 >= api_port >= 0):
        s = None
        t = None
        g = None
        try:
            g = ThreadGetter(redis_host=redis_host, redis_port=redis_port, redis_password=redis_password,
                             redis_database=redis_database, need_log=need_getter_log, storage=proxypool_storage)
            t = ThreadTester(redis_host=redis_host, redis_port=redis_port, redis_password=redis_password,
                             redis_database=redis_database, need_log=need_tester_log, storage=proxypool_storage)
            s = ThreadServer(host=api_host, port=api_port, threaded=True)
            g.setDaemon(set_daemon)
            t.setDaemon(set_daemon)
            s.setDaemon(set_daemon)
            g.start()
            t.start()
            s.start()
        except Exception as e:
            log("proxypool线程异常{}".format(e))
        proxy_test = ""
        url = HTTP + api_host + COLON_SEPARATOR + str(api_port) + "/random"
        is_ip_flag = False
        log("所有线程启动，测试是否已经有代理.......")
        while len(proxy_test) == 0 or (not is_ip_flag):
            try:
                proxy_test = requests.get(url, timeout=(20, 20)).text
                is_ip_flag = is_ip(proxy_test)
            except Exception as e:
                log("测试proxypool项目报错:{}".format(e))
                proxy_test = ""
            time.sleep(2)
        if len(proxy_pool_url) == 0:
            PROXY_POOL_URL = url
        log("启动proxypool完成")
        PROXY_POOL_CAN_RUN_FLAG = False
        return s, g, t
    else:
        if require_proxy_pool and PROXY_POOL_CAN_RUN_FLAG:
            log("redis或者Flask配置错误")
            return ()
        elif require_proxy_pool and not PROXY_POOL_CAN_RUN_FLAG:
            log("无法重复启动proxypool")
            return ()
        elif not require_proxy_pool:
            return ()
        return ()


def get_split(lens: int = 20, style: str = '=') -> str:
    """
    get a series of splits,like "======"
    :param lens: the length of split string
    :param style: the char used to create split string
    :return: a string of split
    """
    s = ''
    lens = max(lens, 1)
    for i in range(lens):
        s = s + style
    return s


def get_proxy() -> str or None:
    """
    get a proxy from proxy url which create by me to collect
    ip proxies
    :return:
    """
    if len(PROXY_POOL_URL) <= 0:
        log("使用了代理（require_proxy=Ture）,但是没有设置代理连接")
        log("请使用basic_config(proxy_pool_url=\"\")设置")
        raise Exception("无法获取代理连接")
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
    except ConnectionError as e:
        log(e)
        return None


def two_one_choose(p: int = 0.5) -> bool:
    """
    :parameter p:概率, 0 <= p <= 1
    :return: return a bool value which decide whether choose two choices
    """
    k = random.randint(0, 10)
    if k >= p * 10:
        return True
    else:
        return False


def local_path_generate(folder_name: str, file_name: str = "",
                        suffix: str = ".pdf", need_log: bool = True) -> str:
    """
    create a folder whose name is folder_name in folder which code in if folder_name
    is not exist. and then concat pdf_name to create file path.
    :param need_log: 是否需要日志，不影响重要信息输出
    :param suffix: 自动命名时文件后缀
    :param folder_name: 待创建的文件夹名称
    :param file_name: 文件名称，带后缀格式
    :return: 返回文件绝对路径
    """
    if folder_name is None or len(folder_name) == 0:
        folder_name = os.path.abspath(".")
    try:
        if os.path.exists(folder_name):
            if need_log:
                log("文件夹{}存在".format(folder_name))
        else:
            os.makedirs(folder_name)
    except Exception as e:
        log("创建文件夹{}失败".format(e))
    if len(file_name) == 0:
        file_name = str(time.strftime("%H_%M_%S", time.localtime()))
        file_name = file_name + str(random.randint(10000, 99999))
        file_name = file_name + suffix
    dir = os.path.abspath(folder_name)
    work_path = os.path.join(dir, file_name)
    return work_path


def write_file(path: str, mode: str, string: str, encoding: str = "utf-8") -> None:
    try:
        with open(path, mode=mode, encoding=encoding) as f:
            f.write(string)
        f.close()
        log("写入文件{}成功".format(path))
    except Exception as e:
        log("写入文件{}失败：{}".format(path, e))


def cookieString2CookieJar(cookie: str = "") -> RequestsCookieJar:
    """
    将字符串形式的cookie转成RequestsCookieJar
    :param cookie: 待转换的cookie字符串
    :return: RequestsCookieJar 对象
    """
    if len(cookie) == 0:
        log("cookie为空，返回空值")
        return RequestsCookieJar()
    cookie = cookie.replace(" ", "")
    cookies = cookie.split(";")
    cookie_dict = {}
    for c in cookies:
        cookie_list = list(c)
        name = ""
        value = ""
        flag = True
        for item in cookie_list:
            if item == "=" and flag:
                flag = False
                continue
            if flag:
                name = name + item
            else:
                value = value + item
        if len(name) != 0 and len(value) != 0:
            cookie_dict[name] = value
    cookie_jar = RequestsCookieJar()
    for item in cookie_dict.items():
        cookie_jar.set(item[0], item[1])
    return cookie_jar


class NoProxyException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return repr("无法获取代理")

    def __repr__(self) -> str:
        return super().__repr__()


class ThreadStopException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return repr("停止线程")

    def __repr__(self) -> str:
        return super().__repr__()


# if __name__ == "__main__":
#     a = CanStopThread()
#     basic_config(logs_style=LOG_STYLE_PRINT)
#     try:
#         a.stop()
#     except ThreadStopException as e:
#         log("线程{}结束".format(a.name))
#     except Exception as e:
#         log("结束线程{}错误{}".format(a.name, e))
#     except BaseException as e:
#         log(e)


