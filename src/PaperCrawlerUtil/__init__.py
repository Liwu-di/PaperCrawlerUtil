import sys
import os
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent))
__all__ = ["common_util", "crawler_util", "document_util"]

from crawler_util import *
from document_util import *
from common_util import *

basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=True)
