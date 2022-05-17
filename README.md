# PaperCrawlerUtil
一套用来爬论文的工具，a collection of utils to get paper
This project is an util package to create a crawler.
It contains many tools which can finish part function.
There is an example:

```python
from PaperCrawlerUtil.crawler_util import *


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
        attr_list = get_attribute_of_html(html,
                                          {'href': "in", 'CVPR': "in", "content": "in", "papers": "in"})
        for eles in attr_list:
            pdf_path = eles.split("<a href=\"")[1].split("\">")[0]
            # local_path_generate 生成文件名绝对路径，要求提供文件夹名称，
            # 文件名不提供则默认使用当前时间作为文件名
            work_path = local_path_generate("cvpr{}".format(times))
            # retrieve_file 获取文件，可以设置是否使用代理等等
            retrieve_file("https://openaccess.thecvf.com/" + pdf_path, work_path)
```
```python
#此外也可以通过doi从sci-hub下载，示例代码如下：
get_pdf_url_by_doi(doi="xxxx", work_path=local_path_generate("./"))
```
```python
#本模块使用自己搭建的一个代理池，代码来自https://github.com/Germey/ProxyPool.git
#也可以自己在本地搭建这样的代理服务器，然后使用如下代码更换代理池
basic_config(proxy_pool_url="http://localhost:xxxx")

#同时可以替换，其他的一些配置，如下所示，其中日志的等级只能配置一次，之后不会再生效
basic_config(log_file_name="1.log",
                 log_level=logging.WARNING,
                 proxy_pool_url="http://xxx",
                 logs_style=LOG_STYLE_LOG)
```

```python
#如下所示，可以抽取路径上的PDF中的信息，其中路径可以是PDF也可以是文件路径，会自动判断
#如果是文件夹，则会遍历所有文件，然后返回总的字符串，可以自选分割符的形式
#同时信息的提取是通过两个标记实现的，即通过开始和结束标记截取字段
title_and_abstract = get_para_from_pdf(path="E:\\git-code\\paper-crawler\\CVPR\\CVPR_2021\\3\\3", ranges=(0, 2))
write_file(path=local_path_generate("E:\\git-code\\paper-crawler\\CVPR\\CVPR_2021\\3\\3", "title_and_abstract.txt"),
               mode="w+", string=title_and_abstract)
```

```commandline
也可以直接安装本包
pip install PaperCrawlerUtil
```

