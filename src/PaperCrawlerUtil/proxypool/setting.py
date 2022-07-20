import platform
from os.path import dirname, abspath, join
from environs import Env
from loguru import logger


env = Env()
env.read_env()

# definition of flags
IS_WINDOWS = platform.system().lower() == 'windows'

# definition of dirs
ROOT_DIR = dirname(dirname(abspath(__file__)))
LOG_DIR = join(ROOT_DIR, env.str('LOG_DIR', 'logs'))

# definition of environments
DEV_MODE, TEST_MODE, PROD_MODE = 'dev', 'test', 'prod'
APP_ENV = env.str('APP_ENV', DEV_MODE).lower()
APP_DEBUG = env.bool('APP_DEBUG', True if APP_ENV == DEV_MODE else False)
APP_DEV = IS_DEV = APP_ENV == DEV_MODE
APP_PROD = IS_PROD = APP_ENV == PROD_MODE
APP_TEST = IS_TEST = APP_ENV == TEST_MODE


# Which WSGI container is used to run applications
# - gevent: pip install gevent
# - tornado: pip install tornado
# - meinheld: pip install meinheld
APP_PROD_METHOD_GEVENT = 'gevent'
APP_PROD_METHOD_TORNADO = 'tornado'
APP_PROD_METHOD_MEINHELD = 'meinheld'
APP_PROD_METHOD = env.str('APP_PROD_METHOD', APP_PROD_METHOD_GEVENT).lower()

# only save anonymous proxy
TEST_ANONYMOUS = env.bool('TEST_ANONYMOUS', True)
# TEST_HEADERS = env.json('TEST_HEADERS', {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
# })
TEST_VALID_STATUS = env.list('TEST_VALID_STATUS', [200, 206, 302])

# definition of api
API_THREADED = env.bool('API_THREADED', True)


ENABLE_LOG_FILE = env.bool('ENABLE_LOG_FILE', True)
ENABLE_LOG_RUNTIME_FILE = env.bool('ENABLE_LOG_RUNTIME_FILE', True)
ENABLE_LOG_ERROR_FILE = env.bool('ENABLE_LOG_ERROR_FILE', True)


LOG_LEVEL_MAP = {
    DEV_MODE: "DEBUG",
    TEST_MODE: "INFO",
    PROD_MODE: "ERROR"
}

LOG_LEVEL = LOG_LEVEL_MAP.get(APP_ENV)

if ENABLE_LOG_FILE:
    if ENABLE_LOG_RUNTIME_FILE:
        logger.add(env.str('LOG_RUNTIME_FILE', join(LOG_DIR, 'runtime.log')),
                   level=LOG_LEVEL, rotation='1 week', retention='20 days')
    if ENABLE_LOG_ERROR_FILE:
        logger.add(env.str('LOG_ERROR_FILE', join(LOG_DIR, 'error.log')),
                   level='ERROR', rotation='1 week')
