# PaperCrawlerUtil
一套用来爬论文的工具，a collection of utils to get paper
This project is an util package to create a crawler.
It contains many tools which can finish part function.
There is an example:

```python
from CrawlerUtil.util import *


basic_config(style="print")
for times in ["2019", "2020", "2021"]:
    html = random_proxy_header_access("https://openaccess.thecvf.com/CVPR{}".format(times), random_proxy=False)
    attr_list = get_attribute_of_html(html, {'href': "in", 'CVPR': "in", "py": "in", "day": "in"})
    for ele in attr_list:
        path = ele.split("<a href=\"")[1].split("\">")[0]
        path = "https://openaccess.thecvf.com/" + path
        html = random_proxy_header_access(path, random_proxy=False)
        attr_list = get_attribute_of_html(html,
                                          {'href': "in", 'CVPR': "in", "content": "in", "papers": "in"})
        for eles in attr_list:
            pdf_path = eles.split("<a href=\"")[1].split("\">")[0]
            work_path = local_path_generate("cvpr{}".format(times))
            retrieve_file("https://openaccess.thecvf.com/" + pdf_path, work_path)

```
```python
也可以直接安装本包
pip install PaperCrawlerUtil
```