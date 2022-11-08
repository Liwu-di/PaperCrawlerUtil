# PaperCrawlerUtil
一套工具组，包括:
1. 爬虫相关： 
   * 访问链接 
   * 获取元素
   * 抽取文件等等
2. 已经实现好的工具
   * 通过scihub获取论文的小工具，
   * 还有对于pdf转doc，
   * 文本翻译,
   * 代理连接获取以及通过api获取代理链接，
   * PDF文件合并，
   * PDF文件截取某些页等  
3. 科研相关
   * 通过给定的数据库连接，自动记录运行代码的时间，结束时间，运行的文件等等

A set of tools , including   
1. crawler utils:  
   1. accessing links  
   2. getting elements  
   3. extracting files, etc.
2. other tools:  
   1. obtain papers through scihub  
   2. pdf to doc  
   3. text translation  
   4. proxy connection acquisition and proxy link acquisition through api  
   5. PDF file merging  
   6. PDF file intercepting certain pages, etc.  
3. Research related
   * Through a given database connection, automatically record the time of running the code, the end time, the running file, etc.
# 安装与使用
```commandline
可以直接安装本包
pip install PaperCrawlerUtil
```

## 基本使用
本项目依赖proxypool项目，该项目可以爬取免费的代理，
[proxy pool项目仓库](https://github.com/Python3WebSpider/ProxyPool)  
感谢大佬为开源社区做出的贡献  
Thanks for supporting of JetBrains Open Source Support project and your free license.   
![jetbrains logo 图片](https://github.com/Liwu-di/PaperCrawlerUtil/blob/main/pic/jb_beam.png)

## 关于代理池
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
```
### ***代理池更新：***  
目前版本迭代已经可以做到仅需要提供redis信息就可以获得一个代理连接，
默认为http://127.0.0.1:5555/random，  
使用方法如下：
```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *

"""
代理连接爬取和检测需要时间，所以刚开始可能会出现代理大量无法使用情况
"""
basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=True,
            redis_host="127.0.0.1",
            redis_port=6379,
            redis_database=0)


```
### ***代理池更新：也可以不使用Redis，直接使用python dict代替，方法如下：***
```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=True, proxypool_storage="dict")

"""
使用dict时，也可以像redis一样，保存数据到硬盘，下次启动再加载，默认保存在dict.db，
可以通过dict_store_path修改路径，如下：
basic_config会返回三个对象，依次为flask server，getter，tester，
这三个对象都有方法save_dict()保存字典
"""
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *

s, g, t = basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=True, need_tester_log=False,
                           need_getter_log=False, proxypool_storage="dict", need_storage_log=False,
                           api_port=5556, set_daemon=True)
time.sleep(10)
t.save_dict()
s.save_dict()
g.save_dict()

"""
其中日志信息比较多，也可以在basic_config中取消日志输出例如：
"""
basic_config(require_proxy_pool=True, need_tester_log=False,
                 need_getter_log=False, need_storage_log=False)
```

### 单独启用代理池(对proxypool项目的一个小扩展，可以直接代码启动，省事)
```python
"""
也可以单独启用代理池，作为其他应用的一部分使用，方法如下：
其中set_daemon必须为False，否则主线程结束之后，子线程也结束了
"""
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=True, need_tester_log=False,
                     need_getter_log=False, proxypool_storage="dict", need_storage_log=False,
                     api_port=5556, set_daemon=False)
```

## 爬虫应用
### 爬取CVPR文章
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
### 爬取EMNLP文章
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
"""
获取文件名
"""
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

### 根据doi从sci-hub下载（测试较少，不一定好用）
```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
#此外也可以通过doi从sci-hub下载，示例代码如下：
get_pdf_url_by_doi(doi="xxxx", work_path=local_path_generate("./"))
```

### 谷歌学术爬虫
```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *

"""
搜素谷歌学术，并且可以下载有PDF链接的文件，
contain_all，contain_complete_sentence，least_contain_one，not_contain和q只需要提供一个，
并且q的优先级高于四个高级查询列表。
必须提供一个可以访问谷歌的代理
"""
contain_all = ["text", "summary"]
contain_complete_sentence = ["prompt", "learning"]
least_contain_one = ["a", "b", "c"]
not_contain = []
google_scholar_search_crawler(contain_all=contain_all, contain_complete_sentence=contain_complete_sentence,
                              least_contain_one=least_contain_one, not_contain=not_contain, need_retrieve_file=True,
                              proxy="127.0.0.1:33210", file_sava_directory="E:\\")
```

## PDF处理
### 截取某些页中PDF文字（比如在前两页中1.introduction之前的所有文字）
这个因为截取出来的文字，如果是左右分栏的，仍然按一栏处理，所以会有混乱，以及图表的注释，效果并不是很好
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

### PDF截取某些页保存为PDF
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
### PDF文件合并为一个大文件
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

## 翻译
### 谷歌以及百度翻译客户端版，注意百度翻译免费额度只有5w了
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
# probability越大，则使用谷歌翻译的概率越大，大于1时，100%使用谷歌翻译
text_translate("", appid, secret_key, is_google=True, probability=1.5)

```

### 谷歌翻译网页版
```python
"""
百度翻译api已经不再免费提供文本翻译，每个月只有5w字符额度，因此请使用谷歌翻译，

"""

from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *

s = ""
for i in range(1000):
    s = s + "i am an apple. "
cookie = "xx"
token = "xx"
#由于在谷歌翻译中，并没有使用token，cookie参数，因此随便填，这里有这个参数只是做统一管理
#后期可以改为对象传值
translate_web(content=s, sl=EN, tl=ZH_CN, proxy="127.0.0.1:33210",
              translate_method=google_trans_final, cookie=cookie, token=token)
```

### 翻译集合类
```python
"""
该类是一个集合类，把一些公用的参数放在init设置，调用时精简代码，内容不变
具体内容可以参考对应的外部函数
"""
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *

basic_config(logs_style=LOG_STYLE_PRINT)
t = Translators(tl=ZH_CN, proxy="127.0.0.1:33210")
s = ""
for i in range(50):
    s = s + "i am an apple"
t.set_param(content=s, total=len(s))
log(t.google_translate_api())
log(get_split())
log(t.sentence_translate_api())
log(get_split())
log(t.web_translator(translate_method=google_trans_final, need_default_reporthook=True))
log(get_split())
log(t.google_translate_web())

"""
链式翻译示例
"""
tt = Translators(proxy="127.0.0.1:33210")
k = tt.chain_translate(content="Traffic flow forecasting or prediction plays an important role in the traffic control and management of a city. Existing works mostly train a model using the traffic flow data of a city and then test the trained model using the data of the same city. It may not be truly intelligent as there are many cities around us and there should be some shared knowledge among different cities. The data of a city and its knowledge can be used to help improve the traffic flow forecasting of other cities. To address this motivation, we study building a universal deep learning model for multi-city traffic flow forecasting. In this paper, we exploit spatial-temporal correlations among different cities with multi-task learning to approach the traffic flow forecasting tasks of multiple cities. As a result, we propose a Multi-city Traffic flow forecasting Network (MTN) via multi-task learning to extract the spatial dependency and temporal regularity among multiple cities later used to improve the performance of each individual city traffic flow forecasting collaboratively. In brief, the proposed model is a quartet of methods: (1) It integrates three temporal intervals and formulates a multi-interval component for each city to extract temporal features of each city; (2) A spatial-temporal attention layer with 3D Convolutional kernels is plugged into the neural networks to learn spatial-temporal relationship; (3) As traffic peak distributions of different cities are often similar, it proposes to use a peak zoom network to learn the peak effect of multiple cities and enhance the prediction performance on important time steps in different cities; (4) It uses a fusion layer to merge the outputs from distinct temporal intervals for the final forecasting results. Experimental results using real-world datasets from DIDI show the superior performance of the proposed model.")

```

## 进度条
```python
"""
以下是使用进度条的一个例子，可以在retrieve_file函数中找到
在urlretrieve中，每次下载一个block的文件，就会调用 reporthook函数，并且传入三个值，
当前块号，块的大小，总量
在其他地方使用时，也可以在函数中增加一个callable 参数，并且传入类似的3个值，再初始化
common_util.process_bar对象，使用对象的process方法进行传参，从而实现进度条的包装
注意：调用之前必须先使用process方法，实现初始化，否则无法达到100%但实际上任务以及成功
"""
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *


# basic_config中，keep_process_bar_style参数默认为真，则使用本
# 模块的log方法时，print_file会强制使用sys.stderr，保持和process_bar
# 使用一样的流，保证进度条始终在最下方
basic_config(logs_style=LOG_STYLE_PRINT)
bar = process_bar()
# 初始化
bar.process(0, 1, 100)
for i in range(100):
  bar.process(0, 1, 100)
  log("ahfu")
  time.sleep(0.1)
```

## CSV文件处理
```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *
"""
csv文件处理，类CsvProcess
"""
filednames = []
with open("C:\\Users\\李武第\\Desktop\\export2022.08.06-07.56.18.csv", mode="r", encoding="utf-8") as f:
    reader = csv.reader(f)
    count = 0
    for row in reader:
        if count >= 1:
            break
        filednames.extend(row)
        count = count + 1
f.close()
# 读取数据
csvp = CsvProcess(file_path="C:\\Users\\李武第\\Desktop\\export2022.08.06-07.56.18.csv")
a = csvp.csv_data(data_format="dict")
b = csvp.csv_data(data_format="list")
# 三种方式写入数据
with open("C:\\Users\\李武第\\Desktop\\a.csv", mode="w+", encoding="utf-8-sig") as f:
    c = csv.DictWriter(f, fieldnames=filednames)
    c.writeheader()
    c.writerows(a)
f.close()
csvp.write_csv(b, write_path="C:\\Users\\李武第\\Desktop\\b.csv")
csvp.write_csv(a, data_format="dict", title=filednames, write_path="C:\\Users\\李武第\\Desktop\\a.csv")

```

## xls文件处理
```python
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.document_util import *

"""
.xls文件处理，类ExcelProcess
"""
basic_config(logs_style=LOG_STYLE_PRINT)
e = ExcelProcess(r"C:\Users\李武第\Desktop\1.xls")
"""
表格内容
id	file_execute  exec_time	finish_time	result	args	other	default1	default2	default3	default4
104	find 2022/1	2022/1	Best Namespace() 90 '' '' '' ''			
"""
for i in range(e.row_size):
  log(e.excel_data(index=i))
"""
输出内容
2022-11-03 10:11:22   ['id', 'file_execute', 'exec_time', 'finish_time', 'result', 'args', 'other', 'default1', 'default2', 'default3', 'default4'] 
2022-11-03 10:11:22   [104.0, 'find', '2022/1', '2022/1', 'Best', 'Namespace()', 90.0, '', '', '', ''] 		
"""

# 写文件
res_list = [[1, 2][3, 4]]
e.write_excel(path=r"C:\\Users\\李武第\\Desktop\\2.xls", content=res_list)
```  

## 科研工具，记录执行情况
```python
from PaperCrawlerUtil.research_util import *
"""
c = {
  "db_url": "数据库的ip地址",
  "db_username": "数据库用户名",
  "pass": "数据库密码",
  "port": "数据库端口",
  "ssl_ip": "如果是云端服务器，需要使用ssl，这里就是服务器ip",
  "ssl_admin": "服务器用户名",
  "ssl_pwd": "服务器密码",
  "ssl_db_port": "服务器上数据库端口",
  "ssl_port": "ssl 端口，一般为22",
  "ignore_error": "是否在数据库记录失败的时候，在本地使用文件记录，默认为True",
  "db_database": "自己建的数据库名称，默认为research",
  "db_table": "自己建的数据表名，默认为record_result，注意自己建表时要继承列，详见方法参数"
}
"""
c = {
        "db_url": "4.x.x.x",
        "db_username": "root",
        "pass": "xxxx",
        "port": 3306,
        "ssl_ip": "4.x.x.x",
        "ssl_admin": "root",
        "ssl_pwd": "xxxx.",
        "ssl_db_port": 3306,
        "ssl_port": 22,
        "ignore_error": True
    }
a = ResearchRecord(**c)
p = a.insert(__file__, get_timestamp())
p = a.update(p, get_timestamp(), "ffdsfsda")
log(p)

# 导出数据
a = ResearchRecord(**c)
k = a.export((100, 200), file_type="xls")

# 生成sql
import ast
# c指的是数据库的配置，这里省略一下，直接用字符串代替命令行传参
c = '{"db_url":"xx.xx.xx.x"}'
# literal_eval 可以吧字符串转成python对象
c = ast.literal_eval(c)
record = ResearchRecord(**c)
kvs = {}
con = {}
# 生成条件和键值对，作为例子
for k in TABLE_TITLE:
  if random.Random().randint(0, 10) > 5:
      kvs[k] = "aaaa"
      con[(k, "156")] = "="
  else:
      kvs[k] = 551
      con[(k, 57275)] = ">"
log(kvs, con)
for p in OP_TYPE:
  log(record.generate_sql(kvs, p, con))
```

## 前后端交互部分
### 科研记录
目前可以使用原生和jquery组成的简单页面进行查看记录
方法是在服务器端启动一个python后端，并且使用nginx进行代理
```commandline
nohup python application.py --port=xxx
```
前端页面见PaperCrawlerUtil/front，直接打开即可
