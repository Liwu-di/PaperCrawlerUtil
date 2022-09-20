import sys
import os
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent))
__all__ = ["common_util", "crawler_util", "document_util", "office_util", "pdf_util"]

from PaperCrawlerUtil.office_util import *
from PaperCrawlerUtil.pdf_util import *
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.document_util import *
from PaperCrawlerUtil.crawler_util import *
from PaperCrawlerUtil.global_val import *
from PaperCrawlerUtil.constant import *
from PaperCrawlerUtil.translate_util import *

basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=False)
