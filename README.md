# PaperCrawlerUtil
一套用来构建小爬虫的工具组，包括访问链接， 获取元素，抽取文件等等
也有已经实现好通过scihub获取论文的小工具，还有对于pdf转doc，文本翻译,代理连接获取以及通过api获取代理链接，
PDF文件合并，PDF文件截取某些页等
A set of tools for building small crawlers, including accessing links, getting elements, extracting files, etc.
There are also small tools that have been implemented to obtain papers through scihub, as well as pdf to doc, text translation, proxy connection acquisition and proxy link acquisition through api,
PDF file merging, PDF file intercepting certain pages, etc.

```commandline
本项目依赖proxypool项目，该项目可以爬取免费的代理，如果不使用该项目，
则需要自己提供代理或者将require_proxy置为False
https://github.com/Python3WebSpider/ProxyPool
感谢大佬为开源社区做出的贡献
#更新：
#目前版本迭代已经可以做到仅需要提供redis信息就可以获得一个代理连接，
#默认为http://127.0.0.1:5555/random，使用方法如下：
basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=True,
            redis_host="127.0.0.1",
            redis_port=6379,
            redis_database=0)
#代理连接爬取和检测需要时间，所以刚开始可能会出现代理大量无法使用情况
#也可以不使用Redis，直接使用python dict代替，方法如下：
basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=True, proxypool_storage="dict")
#其中日志信息比较多，也可以在basic_config中取消日志输出例如：
basic_config(require_proxy_pool=True, need_tester_log=False,
                 need_getter_log=False, need_storage_log=False)
```

```commandline
也可以直接安装本包
pip install PaperCrawlerUtil
```
```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
#本模块使用自己搭建的一个代理池，代码来自https://github.com/Germey/ProxyPool.git
#也可以自己在本地搭建这样的代理服务器，然后使用如下代码更换代理池
basic_config(proxy_pool_url="http://localhost:xxxx")

#同时可以替换，其他的一些配置，如下所示，其中日志的等级只能配置一次，之后不会再生效
basic_config(log_file_name="1.log",
                 log_level=logging.WARNING,
                 proxy_pool_url="http://xxx",
                 logs_style=LOG_STYLE_LOG)
#更新：
#目前版本迭代已经可以做到仅需要提供redis信息就可以获得一个代理连接，
#默认为http://127.0.0.1:5555/random，使用方法如下：
basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=True,
            redis_host="127.0.0.1",
            redis_port=6379,
            redis_database=0)
#代理连接爬取和检测需要时间，所以刚开始可能会出现代理大量无法使用情况

```
```python
"""
更新，增加cookie的访问
"""
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
cookie = "axxxx=c9IxxxxxdK"
html = random_proxy_header_access(
    url="https://s.taobao.com/search?q=iphone5",
    require_proxy=False, cookie=cookie)
```
```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *

basic_config(logs_style="print")
for times in ["2019", "2020", "2021"]:
    # random_proxy_header_access 访问网站并且返回html字符串，其中可以设置是否使用代理等等
    html = random_proxy_header_access("https://openaccess.thecvf.com/CVPR{}".format(times), random_proxy=False)
    # get_attribute_of_html 获取html字符串中所需要的元素，可以配置一个字典，键表示待匹配字符串，值表示规则，还可以选择获取什么样的元素
    # 默认只获取标签<a>
    attr_list = get_attribute_of_html(html, {'href': IN, 'CVPR': IN, "py": IN, "day": IN})
    for ele in attr_list:
        path = ele.split("<a href=\"")[1].split("\">")[0]
        path = "https://openaccess.thecvf.com/" + path
        # 继续访问获取论文地址
        html = random_proxy_header_access(path, random_proxy=False)
        # 同上获取网页元素
        attr_lists = get_attribute_of_html(html,
                                           {'href': "in", 'CVPR': "in", "content": "in", "papers": "in"})
        for eles in attr_lists:
            pdf_path = eles.split("<a href=\"")[1].split("\">")[0]
            # local_path_generate 生成文件名绝对路径，要求提供文件夹名称，
            # 文件名不提供则默认使用当前时间作为文件名
            work_path = local_path_generate("cvpr{}".format(times))
            # retrieve_file 获取文件，可以设置是否使用代理等等
            retrieve_file("https://openaccess.thecvf.com/" + pdf_path, work_path)
```

```python
"""
以下是一个新的例子，用来爬取EMNLP2021的文章，使用了内置代理池，翻译等
"""
from httpcore import SyncHTTPProxy
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=True, need_tester_log=False, need_getter_log=False)
url = "https://aclanthology.org/events/emnlp-2021/"
html = random_proxy_header_access(url, require_proxy=True, max_retry=100, sleep_time=0.5)
pdf = get_attribute_of_html(html, rule={"href": IN, "pdf": IN, "main": IN, "full": NOT_IN, "emnlp": IN})
name = get_attribute_of_html(html,
                             rule={"href": IN, "pdf": NOT_IN, "main": IN, "full": NOT_IN, "emnlp": IN,
                                   "align-middle": IN, "emnlp-main.": IN},
                             attr_list=['strong'])
names = []
for k in name:
    p = list(k)
    q = []
    flag = True
    for m in p:
        if m == "<":
            flag = False
            continue
        if m == ">":
            flag = True
            continue
        if flag:
            q.append(m)
    names.append("".join(q))
pdf_url = []
for p in pdf:
    pdf_url.append(p.split("href=\"")[1].split(".pdf")[0] + ".pdf")
count = 0
proxies = {"https": SyncHTTPProxy((b'http', b'127.0.0.1', 33210, b'')),
           "http": SyncHTTPProxy((b'http', b'127.0.0.1', 33210, b''))}
if len(pdf_url) == len(names):
    for k in range(len(pdf_url)):
        if retrieve_file(url=pdf_url[k],
                         path=local_path_generate("EMNLP2021",
                                                  file_name=sentence_translate(string=names[k],
                                                                               appid="2020031xx99558",
                                                                               secret_key="BxxxJDGBwaZgr4F",
                                                                               max_retry=10,
                                                                               proxies=proxies,
                                                                               probability=0.5,
                                                                               is_google=True) + ".pdf")
                , require_proxy=True):
            count = count + 1

log("count={}".format(str(count)))
```

```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
#此外也可以通过doi从sci-hub下载，示例代码如下：
get_pdf_url_by_doi(doi="xxxx", work_path=local_path_generate("./"))
```

```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
#如下所示，可以抽取路径上的PDF中的信息，其中路径可以是PDF也可以是文件路径，会自动判断
#如果是文件夹，则会遍历所有文件，然后返回总的字符串，可以自选分割符的形式
#同时信息的提取是通过两个标记实现的，即通过开始和结束标记截取字段
title_and_abstract = get_para_from_pdf(path="E:\\git-code\\paper-crawler\\CVPR\\CVPR_2021\\3\\3", ranges=(0, 2))
write_file(path=local_path_generate("E:\\git-code\\paper-crawler\\CVPR\\CVPR_2021\\3\\3", "title_and_abstract.txt"),
               mode="w+", string=title_and_abstract)
```

```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
basic_config(logs_style=LOG_STYLE_PRINT)
# 通过百度翻译api平台申请获得
appid = "20200316xxxx99558"
secret_key = "BK6xxxxxDGBwaZgr4F"
# 实现文本翻译， 可以结合上一块代码获取PDF中的文字翻译，注意的是使用了百度
# 和谷歌翻译，因此如果使用谷歌翻译，则需要提供代理，默认会尝试http://127.0.01:1080 这个地址
text_translate("", appid, secret_key, is_google=True)

```

```python
"""
以下是PDF文件分割的一个例子，表示将"D:\python project\PaperCrawlerUtil\EMNLP2021"文件夹下所有PDF文件
截取第一页保存到目录"EMNLP2021_first_page"中，文件名自动生成
"""

from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
getSomePagesFromFileOrDirectory("D:\python project\PaperCrawlerUtil\EMNLP2021", [0], "EMNLP2021_first_page")

```

```python
"""
以下是PDF文件合并的一个例子，表示将"E:\论文阅读\论文\EMNLP\EMNLP2021_first_page"文件夹下所有PDF文件
的第一页合并保存到目录"E:\论文阅读\论文\EMNLP\EMNLP2021_first_page\合并.pdf"中，同时默认以50个文件为分组
生成多个文件
"""

from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
cooperatePdf("E:\论文阅读\论文\EMNLP\EMNLP2021_first_page", [0], "E:\论文阅读\论文\EMNLP\EMNLP2021_first_page\合并.pdf", timeout=-1)

```

