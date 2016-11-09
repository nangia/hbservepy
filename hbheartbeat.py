import uploader
import argparse
import traceback
import os
import logging
import datetime
import time
from logging.config import dictConfig

savedtime = None
authentication = None
executablename = os.path.realpath(__file__)
dirname = os.path.dirname(executablename)
logfilename = os.path.join(dirname, 'hbheartbeat.log')
hbuploader = None
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


def hasThisTimeElapsed(fromtime, hours=24):
    if fromtime is None:
        return True
    nowtime = datetime.datetime.now()
    delta = datetime.timedelta(hours=hours)
    if nowtime > fromtime + delta:
        return True
    return False


def sendHeartBeat():
    global authentication
    global savedtime
    if authentication is None or ((authentication is not None) and
                                  hasThisTimeElapsed(savedtime, hours=24)):
        logger.info("Authenticating")
        try:
            authentication = None
            authentication = hbuploader.login(hb_userid, hb_password)
        except:
            logger.error("login method failed")
            authentication = None
            raise Exception("login method failed")

        if authentication is None:
            raise Exception("HB Authentication failed")
        logger.info("Authentication successful")
        savedtime = datetime.datetime.now()

    success = hbuploader.heartbeat(authentication)
    if not success:
        raise Exception("HB heartbeat failure")
    logger.info("HB heartbeat successful")


parser = argparse.ArgumentParser(description='Send a heartbeat to HB servers')
parser.add_argument('--interval', type=int,
                    help='Seconds after which to send heart beat',
                    default=30 * 60)  # 30 minutes
parser.add_argument('--timetowait', type=int,
                    help='Seconds after which to restart in case of error',
                    default=5 * 60)  # 5 minutes

parser.add_argument('userid', help='Your HB userid')
parser.add_argument('password', help='Your HB password')
parser.add_argument('--httpsproxy', help="https proxy",
                    default=None)

args = parser.parse_args()
hb_userid = args.userid
hb_password = args.password
interval = args.interval
timetowait = args.timetowait
httpsproxy = args.httpsproxy

hbuploader = uploader.HBUploader(httpsproxy=httpsproxy)

while True:
    try:
        # now enter into regular loop for heartbeat
        sendHeartBeat()
        time.sleep(interval)
    except KeyboardInterrupt:
        logger.error("\nKeyboardInterrupt received: exiting")
        break
    except Exception, err:
        logger.error("Generic Exception received")
        logger.error(traceback.format_exc())
        logger.error("Will start again in %d s" % timetowait)
        time.sleep(timetowait)
