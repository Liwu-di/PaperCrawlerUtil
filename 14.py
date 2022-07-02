# -*- coding: utf-8 -*-
# @Time    : 2022/5/29 17:38
# @Author  : 银尘
# @FileName: 14.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
# from src.document_util import *
# from src.crawler_util import *
# from src.common_util import *
from src import *


#basic_config(logs_style=LOG_STYLE_PRINT, proxy_pool_url="http://liwudi.fun:56923/random")
# appid = "20200316000399558"
# secret_key = "BK6HRAv6QJDGBwaZgr4F"
# text_translate("", appid, secret_key)
def _1():
    list = []
    with open("C:\\Users\\李武第\\Desktop\\Annual Meeting of the Association for Computational Linguistics (2020) - ACL Anthology.html",
              "r",
              encoding="utf-8") as f:
        list = f.readlines()
    s = ""
    for k in list:
        s = s + k
    attr_list = get_attribute_of_html(s, {"href": IN, "pdf": IN})
    for k in attr_list:
        url = k.split("href=\"")[1].split(".pdf")[0]
        url = url + ".pdf"
        retrieve_file(url, local_path_generate("ACL2019"))
        get_split()


def _2():
    res = []
    with open("1.txt", "r", encoding="utf-8") as f:
        k = f.readlines()
        count = 0
        for p in k:
            q = ""
            while len(q) == 0:
                q = google_translate(p)
            res.append(p)
            res.append(q)
            count = count + 1
            print("当前进度{},count={}".format(str(count/len(k)), str(count)))
    f.close()
    with open("2.txt", "w+", encoding="utf-8") as f:
        for k in res:
            f.write(k)
            f.write("\n")
    f.close()


def _3():
    a = 'https://aclanthology.org/events/acl-2022/'
    s = time.time()
    h = random_proxy_header_access(a, require_proxy=True, max_retry=10)
    h = get_attribute_of_html(h, rule={"href": IN, "pdf": IN, "long": IN, "full": NOT_IN})
    for k in h:
        k = k.split("href=\"")[1].split(".pdf")[0]
        k = k + ".pdf"
        retrieve_file(k, local_path_generate("ACL2022"), require_proxy=True, random_proxy=True,
                      max_retry=100)
    e = time.time()
    log(e - s)


def _5():
    pdf2docx("E:\\作业\\计算机网络\\期末\\xinyue2009.pdf",
             "E:\\作业\\计算机网络\\期末")


class ThreadGetter(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        log("启动getter")
        Getter().run()


class ThreadTester(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        log("启动tester")
        Tester().run()


class ThreadServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        log("启动server")
        app.run(host=API_HOST, port=API_PORT, threaded=API_THREADED, use_reloader=False)


if __name__ == "__main__":
    try:
        # pool = ProxyPool(thread_id="001", thread_name="proxypool")
        # pool.start()
        # pool.join
        g = ThreadGetter()
        t = ThreadTester()
        s = ThreadServer()
        s.start()
        g.start()
        t.start()

    except Exception as e:
        log("proxypool线程异常{}".format(e))
    basic_config(logs_style=LOG_STYLE_PRINT)
    log(get_split(lens=100))
    proxy_test = ""
    api_host = API_HOST
    api_port = str(API_PORT)
    while len(proxy_test) == 0:
        try:
            proxy_test = requests.get("http://" + api_host + ":" + api_port + "/random", timeout=(20, 20)).text
        except Exception as e:
            log("测试proxypool项目报错:{}".format(e))
            proxy_test = ""
        time.sleep(2)
    log("启动proxypool完成")
