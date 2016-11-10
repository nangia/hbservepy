import requests
from logging.config import dictConfig
import logging
import os
import argparse
import traceback

executablename = os.path.realpath(__file__)
dirname = os.path.dirname(executablename)
logfilename = os.path.join(dirname, 'simpleget.log')
logging_config = dict(
    version=1,
    formatters={
        'fmt': {'format':
                '%(asctime)s:%(name)s:%(levelname)s:%(message)s'}
    },
    handlers={
        'c': {'class': 'logging.StreamHandler',
              'formatter': 'fmt',
              'level': logging.DEBUG},
        'f': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': logging.DEBUG,
            'formatter': 'fmt',
            'filename': logfilename,
            'when': 'midnight'
        }
    },
    root={
        'handlers': ['c', 'f'],
        'level': logging.DEBUG,
    },
)

dictConfig(logging_config)
logger = logging.getLogger()

parser = argparse.ArgumentParser(description='Do a simple get and print')
parser.add_argument('url', help="URL to get")
parser.add_argument('--httpsproxy', help="https proxy",
                    default=None)
parser.add_argument('--timeout', help="timeout in seconds", type=int,
                    default=30)

args = parser.parse_args()
httpsproxy = args.httpsproxy
timeout = args.timeout
url = args.url
proxydict = None
if httpsproxy:
    proxydict = {'https': httpsproxy}

try:
    r = requests.get(url, proxies=httpsproxy, timeout=timeout)
    if r.status_code >= 200 and r.status_code <= 299:
        logger.info("Request to %s successful. Status=%d" %
                    (url, r.status_code))
        print r.text
    else:
        logger.info("Request to %s. Status=%d" %
                    (url, r.status_code))
        print r.text
except:
    logger.error("Request to %s unsuccessful" % url)
    logger.error(traceback.format_exc())
