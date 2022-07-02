# -*- coding: utf-8 -*-
# @Time    : 2022/5/31 22:21
# @Author  : 银尘
# @FileName: title_and_abstract_translate.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
from src import *

basic_config(logs_style=LOG_STYLE_PRINT)
appid = "20210316000399558"
secret_key = "BK6HRAv6QJDGBwaZgr4F"
title_abstract = get_para_from_pdf("E:\\git-code\\paper-crawler\\ACL\\ACL2021")
write_file(path=local_path_generate("E:\\git-code\\paper-crawler\\ACL\\ACL2021", "1.txt"),
           mode="w+", string=title_abstract)
title_abstract = text_translate(local_path_generate("E:\\git-code\\paper-crawler\\ACL\\ACL2021", "1.txt"),
                                appid, secret_key, max_retry=20)
write_file(path=local_path_generate("E:\\git-code\\paper-crawler\\ACL\\ACL2021", "2.txt"),
           mode="w+", string=title_abstract)
