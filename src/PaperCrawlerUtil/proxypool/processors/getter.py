from loguru import logger
from proxypool.storages.redis import RedisClient
from proxypool.setting import PROXY_NUMBER_MAX, NEED_LOG_GETTER
from proxypool.crawlers import __all__ as crawlers_cls
from proxypool.storages.proxy_dict import ProxyDict

class Getter(object):
    """
    getter of proxypool
    """

    def __init__(self, redis_host, redis_port, redis_password, redis_database, storage="redis", need_log=True):
        """
        init db and crawlers
        """
        # self.redis = RedisClient(host=redis_host, port=redis_port, password=redis_password, db=redis_database)
        if storage == "redis":
            self.conn = RedisClient(host=redis_host, port=redis_port, password=redis_password, db=redis_database)
        else:
            self.conn = ProxyDict()
        self.crawlers_cls = crawlers_cls
        self.crawlers = [crawler_cls() for crawler_cls in self.crawlers_cls]
        self.need_log = need_log

    def is_full(self):
        """
        if proxypool if full
        return: bool
        """
        return self.conn.count() >= PROXY_NUMBER_MAX

    @logger.catch
    def run(self):
        """
        run crawlers to get proxy
        :return:
        """
        if self.is_full():
            return
        for crawler in self.crawlers:
            if self.need_log:
                logger.info(f'crawler {crawler} to get proxy')
            for proxy in crawler.crawl():
                self.conn.add(proxy)


if __name__ == '__main__':
    getter = Getter()
    getter.run()
