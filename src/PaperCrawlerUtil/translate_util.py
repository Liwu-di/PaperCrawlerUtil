# -*- coding: utf-8 -*-
# @Time    : 2022/8/7 15:41
# @Author  : 银尘
# @FileName: translate_util.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
from typing import Callable

from PaperCrawlerUtil import random_proxy_header_access
from common_util import *
import urllib
from httpcore import SyncHTTPProxy
import hashlib
import http
import json
import time
from googletrans import Translator
import execjs


def baidu_translate(string: str,
                    appid: str,
                    secret_key: str,
                    src: str = "auto",
                    dst: str = "zh",
                    sleep_time: float = 1.2,
                    need_log: bool = True) -> str:
    """
    百度翻译
    :param need_log: 是否需要日志
    :param string:
    :param appid:
    :param secret_key:
    :param src:
    :param dst:
    :param sleep_time:
    :return:
    """
    if need_log:
        log("使用百度翻译")
    httpClient = None
    myurl = '/api/trans/vip/translate'
    fromLang = src  # 原文语种
    toLang = dst  # 译文语种
    salt = random.randint(32768, 65536)
    q = string
    sign = appid + q + str(salt) + secret_key
    sign = hashlib.md5(sign.encode()).hexdigest()
    myurl = myurl + '?appid=' + appid + '&q=' + urllib.parse.quote(
        q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(
        salt) + '&sign=' + sign
    result = {}
    try:
        httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
        httpClient.request('GET', myurl)
        response = httpClient.getresponse()
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)
        time.sleep(sleep_time)
    except Exception as e:
        log(string=e, print_file=sys.stderr)
        time.sleep(sleep_time)
    finally:
        if httpClient:
            httpClient.close()
    res = ""
    try:
        res = result["trans_result"][0]["dst"]
    except Exception as e:
        log(string="翻译错误：{}".format(e), print_file=sys.stderr)
    return res


def google_translate(string: str, src: str = 'en', dest: str = 'zh-cn',
                     proxies: str = None, sleep_time: float = 1.2, need_log: bool = True) -> str:
    """
    谷歌翻译
    @todo 提供一个源语言和目的语言的表
    :param need_log: 是否需要日志
    :param string:
    :param src:
    :param dest:
    :param proxies:
    :param sleep_time:
    :return:
    """
    urls = ['translate.google.cn', 'translate.google.com']
    if proxies is None:
        proxies = {"https": SyncHTTPProxy((b'http', b'127.0.0.1', 1080, b'')),
                   "http": SyncHTTPProxy((b'http', b'127.0.0.1', 1080, b''))}
    if need_log:
        log("使用谷歌翻译")
    try:
        translator = Translator(service_urls=urls, proxies=proxies)
        trans = translator.translate(string, src=src, dest=dest)
        time.sleep(sleep_time)
        return trans.text
    except Exception as e:
        log(string="翻译错误：{}".format(e), print_file=sys.stderr)
        time.sleep(sleep_time)
    return ""


def sentence_translate(string: str, appid: str, secret_key: str,
                       max_retry: int = 10, proxies: str = None,
                       probability: float = 0.5, is_google: bool = True,
                       need_log: bool = True, sleep_time: float = 1.2) -> str:
    """
    随机使用百度谷歌翻译句子
    :param sleep_time: 休眠时间
    :param need_log: 是否需要日志
    :param string: 待翻译语句
    :param appid: 百度翻译appid
    :param secret_key: 百度翻译密钥
    :param max_retry: 最大尝试次数
    :param proxies: 代理，例如：proxies = {"https": SyncHTTPProxy((b'http', b'127.0.0.1', 1080, b'')),
                   "http": SyncHTTPProxy((b'http', b'127.0.0.1', 1080, b''))}
    :param probability: 百度和谷歌翻译之间使用的比例，这个值趋向1则使用谷歌翻译概率大，否则使用百度翻译概率大
    :param is_google: 是否使用谷歌翻译
    :return:
    """
    for i in range(max_retry):
        res = ""
        if is_google:
            if two_one_choose(probability):
                res = baidu_translate(string, appid, secret_key, need_log=need_log, sleep_time=sleep_time)
            else:
                res = google_translate(string, proxies=proxies, need_log=need_log, sleep_time=sleep_time)
            if len(res) == 0:
                continue
            else:
                return res
        else:
            res = baidu_translate(string, appid, secret_key)
            if len(res) == 0:
                continue
            else:
                return res
    return ""


def text_translate(path: str,
                   appid: str,
                   secret_key: str,
                   max_retry: int = 10,
                   is_google: bool = True,
                   probability: float = 0.5,
                   proxies: str = None) -> str:
    """
    文本翻译，根据提供的文件地址，翻译文件内容
    :param path: 文本路径
    :param appid: 百度翻译appid
    :param secret_key: 百度翻译密钥
    :param max_retry: 最大尝试次数
    :param is_google: 是否使用谷歌翻译
    :param proxies: 代理，样例 proxies = {"https": SyncHTTPProxy((b'http', b'127.0.0.1', 33210, b'')),
               "http": SyncHTTPProxy((b'http', b'127.0.0.1', 33210, b''))}
    :param probability:百度和谷歌翻译之间使用的比例，这个值趋向1则使用谷歌翻译概率大，否则使用百度翻译概率大
    :return:
    """
    line = ""
    res = ""
    if is_google and proxies is None:
        log("使用谷歌翻译，但是没有提供代理，尝试使用代理：{'http': 'http://127.0.0.1:1080'}")
        proxies = {'http': 'http://127.0.0.1:1080'}
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for ele in lines:
            line = line + ele
            if len(line) >= 3000:
                line = line.replace("\n", " ")
                res = res + sentence_translate(line, appid, secret_key, max_retry, proxies, probability, is_google)
                line = ""
    f.close()
    if len(line) > 0:
        res = res + sentence_translate(line, appid, secret_key, max_retry, proxies, probability, is_google)
    return res


class Py4Js:

    def __init__(self):
        self.ctx = execjs.compile(""" 
        function TL(a) { 
        var k = ""; 
        var b = 406644; 
        var b1 = 3293161072; 

        var jd = "."; 
        var $b = "+-a^+6"; 
        var Zb = "+-3^+b+-f"; 

        for (var e = [], f = 0, g = 0; g < a.length; g++) { 
            var m = a.charCodeAt(g); 
            128 > m ? e[f++] = m : (2048 > m ? e[f++] = m >> 6 | 192 : (55296 == (m & 64512) && g + 1 < a.length && 56320 == (a.charCodeAt(g + 1) & 64512) ? (m = 65536 + ((m & 1023) << 10) + (a.charCodeAt(++g) & 1023), 
            e[f++] = m >> 18 | 240, 
            e[f++] = m >> 12 & 63 | 128) : e[f++] = m >> 12 | 224, 
            e[f++] = m >> 6 & 63 | 128), 
            e[f++] = m & 63 | 128) 
        } 
        a = b; 
        for (f = 0; f < e.length; f++) a += e[f], 
        a = RL(a, $b); 
        a = RL(a, Zb); 
        a ^= b1 || 0; 
        0 > a && (a = (a & 2147483647) + 2147483648); 
        a %= 1E6; 
        return a.toString() + jd + (a ^ b) 
    }; 

    function RL(a, b) { 
        var t = "a"; 
        var Yb = "+"; 
        for (var c = 0; c < b.length - 2; c += 3) { 
            var d = b.charAt(c + 2), 
            d = d >= t ? d.charCodeAt(0) - 87 : Number(d), 
            d = b.charAt(c + 1) == Yb ? a >>> d: a << d; 
            a = b.charAt(c) == Yb ? a + d & 4294967295 : a ^ d 
        } 
        return a 
    } 
    """)

    def getTk(self, text):
        return self.ctx.call("TL", text)


def google_trans_final(content: str = "", sl: str = AUTO, tl: str = EN,
                       proxy: str = "127.0.0.1:1080", reporthook: Callable[[], None] = None,
                       total: int = 0, need_log: bool = True, cookie: str = "", token: str = "") -> str:
    """
        网页版谷歌翻译，需要提供可以访问谷歌的代理
        :param token: not used
        :param cookie: not used
        :param total: 翻译总数量
        :param content: 待翻译内容
        :param sl: 源语言
        :param tl: 目标语言
        :param proxy: 代理
        :param reporthook: 完成翻译后使用的函数，这里默认使用内置进度条
        :param need_log: 是否需要打印日志，翻译结果等
        :return: 翻译后的文本
        """
    js = Py4Js()
    tk = js.getTk(content)
    url = "http://translate.google.com/translate_a/single?client=t"
    url = url + "&sl=" + sl + "&tl=" + tl
    url = url + ("&hl=en&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw")
    url = url + ("&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&clearbtn=1&otf=1")
    url = url + ("&pc=1&srcrom=0&ssel=0&tsel=0&kc=2&tk=%s&q=%s" % (tk, content))
    html = random_proxy_header_access(url=url, proxy=proxy, require_proxy=True,
                                      random_proxy=False, return_type="object", need_log=False)
    ret = ''
    try:
        trans = html.json()[0]
        for i in range(len(trans)):
            line = trans[i][0]
            if line is not None:
                ret += trans[i][0]
        if reporthook:
            reporthook(0, 1000, total)
    except Exception as e:
        if need_log:
            log("翻译错误：{}".format(e), print_file=sys.stderr)
    return ret


def translate_web(content: str = "", sl: str = AUTO, tl: str = EN,
                  proxy: str = "127.0.0.1:1080", sleep_time: float = 2,
                  need_log: bool = True, translate_method: Callable[[], str] = None,
                  cookie: str = "", token: str = "", reporthook: Callable[[], None] = None,
                  need_default_reporthook: bool = False):
    """
    网页版翻译接口，可以通过translate_method传入需要调用的翻译接口，如果为谷歌翻译需要提供可以访问谷歌的代理
    :param need_default_reporthook: 是否需要默认的报告函数，默认为进度条，初始值False
    :param reporthook: 报告函数
    :param token: token
    :param cookie: cookie
    :param translate_method: 需要调用的翻译方法，需要接受的参数包括：
    content, sl, tl, proxy, total, reporthook, need_log, cookie, token
    :param content: 待翻译内容
    :param sl: 源语言
    :param tl: 目标语言
    :param proxy: 代理
    :param sleep_time: 每次访问翻译睡眠时间
    :param need_log: 是否需要打印日志，翻译结果等
    :return: 翻译后的文本
    """
    res_trans = ""
    count = 0
    sum = len(content)
    if reporthook is None and need_default_reporthook:
        p = process_bar(desc="翻译进度：", final_prompt="翻译完成", total=sum)
        p.process(0, 1000, sum)
        reporthook = p.process
    else:
        reporthook = reporthook
    if len(content) > 1000:
        while len(content) > 1000:
            temp = content[0:999]
            content = content[1000:]
            temp_trans = translate_method(content=temp, sl=sl, tl=tl, proxy=proxy, total=sum,
                                          reporthook=reporthook, need_log=need_log, cookie=cookie,
                                          token=token)
            res_trans = res_trans + temp_trans
            count = count + 1
            time.sleep(sleep_time)
        temp_trans = translate_method(content=content, sl=sl, tl=tl, proxy=proxy, total=sum,
                                      need_log=need_log, cookie=cookie, reporthook=reporthook,
                                      token=token)
        res_trans += temp_trans
        if need_log:
            log(res_trans)
        return res_trans
    else:
        time.sleep(sleep_time)
        res_trans = translate_method(content=content, sl=sl, tl=tl, proxy=proxy, total=sum,
                                     need_log=need_log, cookie=cookie, reporthook=reporthook,
                                     token=token)
        if need_log:
            log(res_trans)
        return res_trans