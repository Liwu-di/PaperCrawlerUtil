import sys

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

from proxypool.processors.getter import Getter
from proxypool.processors.server import app
from proxypool.processors.tester import Tester

PROXY_POOL_URL = ""
logging.basicConfig(filename='crawler_util.log', level=logging.WARNING)
log_style = "log"
HTTP = "http://"
COLON_SEPARATOR = ":"

EQUAL = "equal"
NOT_EQUAL = "not equal"
IN = "in"
NOT_IN = "not in"
LESS_THAN = "less than"
MORE_THAN = "more than"
GREATER_AND_EQUAL = "greater and equal"
LESS_THAN_AND_EQUAL = "less than and equal"

LOG_STYLE_LOG = "log"
LOG_STYLE_PRINT = "print"
LOG_STYLE_ALL = "all"

NEED_CRAWLER_LOG = False
NEED_COMMON_LOG = False
NEED_DOCUMENT_LOG = False

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


class ThreadGetter(threading.Thread):
    def __init__(self, redis_host, redis_port, redis_password, redis_database, need_log: bool = True):
        threading.Thread.__init__(self)
        self.need_log = need_log
        self.host = redis_host
        self.port = redis_port
        self.password = redis_password
        self.database = redis_database

    def run(self):
        log("启动getter")
        Getter(redis_host=self.host, redis_port=self.port,
               redis_password=self.password, redis_database=self.database, need_log=self.need_log).run()


class ThreadTester(threading.Thread):
    def __init__(self, redis_host, redis_port, redis_password, redis_database, need_log: bool = True):
        threading.Thread.__init__(self)
        self.need_log = need_log
        self.host = redis_host
        self.port = redis_port
        self.password = redis_password
        self.database = redis_database

    def run(self):
        log("启动tester")
        Tester(redis_host=self.host, redis_port=self.port,
               redis_password=self.password, redis_database=self.database, need_log=self.need_log).run()


class ThreadServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        log("启动server")
        app.run(host=API_HOST, port=API_PORT, threaded=API_THREADED, use_reloader=False)


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
                 need_tester_log: bool = True) -> None:
    """
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
    global NEED_CRAWLER_LOG, NEED_COMMON_LOG, NEED_DOCUMENT_LOG
    global log_style
    PROXY_POOL_URL = proxy_pool_url
    log_style = logs_style
    if require_proxy_pool and PROXY_POOL_CAN_RUN_FLAG and len(
            redis_host) > 0 and 0 <= redis_database <= 65535 and 0 <= redis_port <= 65535:
        try:
            g = ThreadGetter(redis_host=redis_host, redis_port=redis_port, redis_password=redis_password,
                             redis_database=redis_database, need_log=need_getter_log)
            t = ThreadTester(redis_host=redis_host, redis_port=redis_port, redis_password=redis_password,
                             redis_database=redis_database, need_log=need_tester_log)
            s = ThreadServer()
            g.start()
            t.start()
            s.start()
        except Exception as e:
            log("proxypool线程异常{}".format(e))
        proxy_test = ""
        api_host = API_HOST
        api_port = str(API_PORT)
        url = HTTP + api_host + COLON_SEPARATOR + api_port + "/random"
        while len(proxy_test) == 0:
            try:
                proxy_test = requests.get(url, timeout=(20, 20)).text
            except Exception as e:
                log("测试proxypool项目报错:{}".format(e))
                proxy_test = ""
            time.sleep(2)
        if len(proxy_pool_url) == 0:
            PROXY_POOL_URL = url
        log("启动proxypool完成")
        PROXY_POOL_CAN_RUN_FLAG = False


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


def local_path_generate(folder_name: str, file_name: str = "", suffix: str = ".pdf") -> str:
    """
    create a folder whose name is folder_name in folder which code in if folder_name
    is not exist. and then concat pdf_name to create file path.
    :param suffix: 自动命名时文件后缀
    :param folder_name: 待创建的文件夹名称
    :param file_name: 文件名称，带后缀格式
    :return: 返回文件绝对路径
    """
    if folder_name is None or len(folder_name) == 0:
        folder_name = os.path.abspath(".")
    try:
        if os.path.exists(folder_name):
            if NEED_COMMON_LOG:
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


class NoProxyException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return repr("无法获取代理")

    def __repr__(self) -> str:
        return super().__repr__()

# if __name__ == "__main__":
#     pool = ProxyPool(thread_id="001", thread_name="proxypool")
#     pool.start()
#     print("123")
