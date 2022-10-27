import sys
import os
import pathlib
from PaperCrawlerUtil.common_util import basic_config
sys.path.append(str(pathlib.Path(__file__).parent))
__all__ = ["common_util", "crawler_util", "document_util", "office_util", "pdf_util", "research_util"]
__author__ = "liwudi@liwudi.fun"
__version__ = "0.1.21"
__github__ = "https://github.com/Liwu-di/PaperCrawlerUtil"
__email__ = "a154125960@gmail.com"

basic_config()
