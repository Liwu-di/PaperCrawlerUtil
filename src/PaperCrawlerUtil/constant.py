# -*- coding: utf-8 -*-
# @Time    : 2022/7/16 11:39
# @Author  : 银尘
# @FileName: constant.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun

"""
跨文件全局变量名定义
"""
REDIS_CONF = "REDIS"
STORAGE_CONF = "storage"
CROSS_FILE_GLOBAL_DICT_CONF = "global_dict"
STORAGE_LOG_CONF = "storage_log"
GETTER_LOG_CONF = "getter_log"
TESTER_LOG_CONF = "tester_log"
PROXY_SCORE_MAX = "max_score"
PROXY_SCORE_MIN = "min_score"
PROXY_SCORE_INIT = "init_score"
POOL_MAX = "pool_max"
POOL_MIN = "pool_min"
DICT_STORE_PATH = "dict_store_path"
TEST_BATCH_NUM = "test_batch_num"
TESTER_CYCLE = "tester cycle"
GETTER_CYCLE = "getter cycle"
TESTER_TIMEOUT = "test_timeout"
GETTER_TIMEOUT = "getter_timeout"
TESTER_URL = "tester url"
API_HOST = "api host"
API_PORT = "api port"


"""
存储方式定义
"""
STORAGE_REDIS = "redis"
STORAGE_DICT = "dict"

"""
比较方式定义
"""
EQUAL = "equal"
NOT_EQUAL = "not equal"
IN = "in"
NOT_IN = "not in"
LESS_THAN = "less than"
MORE_THAN = "more than"
GREATER_AND_EQUAL = "greater and equal"
LESS_THAN_AND_EQUAL = "less than and equal"

"""
日志定义方式
"""
LOG_STYLE_LOG = "log"
LOG_STYLE_PRINT = "print"
LOG_STYLE_ALL = "all"

"""
特殊符号，字符串
"""
HTTP = "http://"
COLON_SEPARATOR = ":"
BAIDU = "http://www.baidu.com"

"""
HTTP 访问方式
"""

POST = "POST"
GET = "GET"
DELETE = "DELETE"
OPTIONS = "OPTIONS"
HEAD = "HEAD"
PUT = "PUT"
PATCH = "PATCH"
