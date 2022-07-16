from flask import Flask, g

import global_val
from proxypool.exceptions import PoolEmptyException
from proxypool.storages.redis import RedisClient
from global_val import *
from proxypool.storages.proxy_dict import ProxyDict
from constant import *

IS_DEV = True

__all__ = ['app']

app = Flask(__name__)
if IS_DEV:
    app.debug = True


def get_conn():
    """
    get redis client object
    :return:
    """
    if not hasattr(g, 'conn'):
        if global_val.get_value(STORAGE_CONF) == STORAGE_REDIS:
            redis_conf = global_val.get_value(REDIS_CONF)
            g.conn = RedisClient(host=redis_conf[0], port=redis_conf[1], password=redis_conf[2], db=redis_conf[3])
        else:
            g.conn = ProxyDict()
    return g.conn


@app.route('/')
def index():
    """
    get home page, you can define your own templates
    :return:
    """
    return '<h2>Welcome to Proxy Pool System</h2>'


@app.route('/random')
def get_proxy():
    """
    get a random proxy
    :return: get a random proxy
    """
    conn = get_conn()
    try:
        res = conn.random().string()
        return res
    except PoolEmptyException as e:
        print("代理池无代理，等待......")
        return ""
    except Exception as e:
        return ""
        raise e



@app.route('/all')
def get_proxy_all():
    """
    get all proxy
    :return: all proxy list
    """
    conn = get_conn()
    proxies = conn.all()
    proxies_string = ''
    if proxies:
        for proxy in proxies:
            proxies_string += str(proxy) + '\n'

    return proxies_string


@app.route('/count')
def get_count():
    """
    get the count of proxies
    :return: count, int
    """
    conn = get_conn()
    return str(conn.count())

@app.route("/test")
def testDict():
    """
    用来测试dict方式，redis模式启动时，无意义
    :return:
    """
    if global_val.get_value(STORAGE_CONF) == STORAGE_REDIS:
        return STORAGE_REDIS
    else:
        s = ""
        for i in get_conn().dict.items():
            s = s + i[0]
        return s


# if __name__ == '__main__':
#     API_HOST = global_val.get_value("API_HOST")
#     API_PORT = global_val.get_value("API_PORT")
#     API_THREADED = global_val.get_value("API_THREADED")
#     app.run(host=API_HOST, port=API_PORT, threaded=API_THREADED)
