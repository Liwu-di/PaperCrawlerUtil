import sys
import os
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent))
__all__ = ["common_util", "crawler_util", "document_util", "office_util", "pdf_util"]
__author__ = "liwudi@liwudi.fun"
__version__ = "0.1.7"
__github__ = "https://github.com/Liwu-di/PaperCrawlerUtil"
__email__ = "a154125960@gmail.com"

from PaperCrawlerUtil.common_util import basic_config
basic_config()
