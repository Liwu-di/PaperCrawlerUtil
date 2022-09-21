from retrying import RetryError, retry
import requests
from loguru import logger
from constant import *
import PaperCrawlerUtil.global_val
from fake_headers import Headers
import time


class BaseCrawler(object):
    urls = []

    @retry(stop_max_attempt_number=3, retry_on_result=lambda x: x is None, wait_fixed=2000)
    def fetch(self, url, **kwargs):
        try:
            headers = Headers(headers=True).generate()
            kwargs.setdefault('timeout', global_val.get_value(GETTER_TIMEOUT))
            kwargs.setdefault('verify', False)
            kwargs.setdefault('headers', headers)
            response = requests.get(url, **kwargs)
            if response.status_code == 200:
                response.encoding = 'utf-8'
                return response.text
        except (requests.ConnectionError, requests.ReadTimeout):
            return

    def process(self, html, url):
        """
        used for parse html
        """
        for proxy in self.parse(html):
            crawler_log = global_val.get_value(GETTER_LOG_CONF)
            if crawler_log:
                logger.info(f'fetched proxy {proxy.string()} from {url}')
            yield proxy

    def crawl(self):
        """
        crawl main method
        """
        crawler_log = global_val.get_value(GETTER_LOG_CONF)
        try:
            for url in self.urls:
                if crawler_log:
                    logger.info(f'fetching {url}')
                html = self.fetch(url)
                if not html:
                    continue
                time.sleep(.5)
                yield from self.process(html, url)
        except RetryError:
            logger.error(
                f'crawler {self} crawled proxy unsuccessfully, '
                'please check if target url is valid or network issue')
