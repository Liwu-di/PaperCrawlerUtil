import logging
import os
import random
import time

import requests

PROXY_POOL_URL = "http://liwudi.fun:56923/random"
logging.basicConfig(filename='../my.log', level=logging.WARNING)
log_style = "log"

EQUAL = "equal"
NOT_EQUAL = "not equal"
IN = "in"
NOT_IN = "not in"

LOG_STYLE_LOG = "log"
LOG_STYLE_PRINT = "print"
LOG_STYLE_ALL = "all"


def log(string):
    global log_style
    if log_style == LOG_STYLE_LOG:
        logging.warning(string)
    elif log_style == LOG_STYLE_PRINT:
        print(string)
    elif log_style == LOG_STYLE_ALL:
        logging.warning(string)
        print(string)


def basic_config(log_file_name="../my.log", log_level=logging.WARNING,
                 proxy_pool_url="http://liwudi.fun:56923/random",
                 logs_style="log"):
    """

    :param log_file_name: 日志文件名称
    :param log_level: 日志等级
    :param proxy_pool_url: 代理获取地址
    :param logs_style: log表示使用日志文件，print表示使用控制台，all表示两者都使用
    :return:
    """
    global PROXY_POOL_URL
    global log_style
    PROXY_POOL_URL = proxy_pool_url
    log_style = logs_style


def get_split(lens=20, style='='):
    """
    get a series of splits,like "======"
    :param lens: the length of split string
    :param style: the char used to create split string
    :return: a string of split
    """
    s = ''
    for i in range(lens):
        s = s + style
    return s


def get_proxy():
    """
    get a proxy from proxy url which create by me to collect
    ip proxies
    :return:
    """
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
    except ConnectionError as e:
        log(e)
        return None


def two_one_choose(p=0.5):
    """
    :parameter p:概率, 0 <= p <= 1
    :return: return a bool value which decide whether choose two choices
    """
    k = random.randint(0, 10)
    if k >= p * 10:
        return True
    else:
        return False


def local_path_generate(folder_name, file_name="", suffix=".pdf"):
    """
    create a folder whose name is folder_name in folder which code in if folder_name
    is not exist. and then concat pdf_name to create file path.
    :param suffix: 自动命名时文件后缀
    :param folder_name: 待创建的文件夹名称
    :param file_name: 文件名称，带后缀格式
    :return: 返回文件绝对路径
    """
    try:
        if os.path.exists(folder_name):
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


def write_file(path, mode, string, encoding="utf-8"):
    try:
        with open(path, mode=mode, encoding=encoding) as f:
            f.write(string)
        f.close()
        log("写入文件{}成功".format(path))
    except Exception as e:
        log("写入文件{}失败：{}".format(path, e))
