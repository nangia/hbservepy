import pika
import msgpack
import tempfile
import uploader
import argparse
import urlparse
import time
import traceback
import os
import logging
import datetime
from logging.config import dictConfig
import sys
from configreader import ConfigReader

hb_userid = ""
hb_password = ""
rabbitmq_password = ""
url_str = "amqp://guest@localhost//"
queue_name = "report_queue"
tmpDirName = "tmp"
count = 0
configreader = None
hbuploader = None

authmap = {}
savedtime = None
connection = None

executablename = os.path.realpath(__file__)
dirname = os.path.dirname(executablename)
logfilename = os.path.join(dirname, 'processmsg.log')
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
# logconfigfile = os.path.join(dirname, 'processmsglog.ini')

# if not os.path.exists(logconfigfile):
#    print "%s does not exist. Exiting" % logconfigfile
# fileConfig(logconfigfile)
dictConfig(logging_config)

logger = logging.getLogger()

tmpDirFullPath = os.path.join(dirname, tmpDirName)
logger.info("tmpDir = %s" % tmpDirFullPath)

if not os.path.isdir(tmpDirFullPath) or not os.path.exists(tmpDirFullPath):
    logger.error("%s does not exist. Exiting" % tmpDirFullPath)
    sys.exit(-1)
# loglevel = args.log
# numeric_level = getattr(logger, loglevel.upper(), None)
# if not isinstance(numeric_level, int):
#     raise ValueError('Invalid log level: %s' % loglevel)
# print "loglevel (%s) = %d" % (loglevel, numeric_level)
# print "logfile = %s" % logfile
# logger.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
#                     filename=logfile, level=numeric_level)
# #                        format= %(message)s')


def hasThisTimeElapsed(fromtime, hours=24):
    if fromtime is None:
        return True
    nowtime = datetime.datetime.now()
    delta = datetime.timedelta(hours=hours)
    if nowtime > fromtime + delta:
        return True
    return False


def getTempFile():
    return tempfile.NamedTemporaryFile(dir=tmpDirFullPath,
                                       delete=False, suffix=".pdf")


def processMsg(msg):
    global authmap
    global count
    global savedtime
    count = count + 1
    logger.info("========Starting processing %d =========" % count)
    tuple = msgpack.unpackb(msg)
    (testdate, phone, description, name, email, fileblob, sid,
     pid, labid) = tuple
    logger.info("processMsg: processing %s for %s" % (description, phone))
    tempfile = getTempFile()
    tempfile.write(fileblob)
    tempfile.close()
    fmt = "testdate=%s phone=%s description=%s name=%s " + \
          "email=%s file=%s sid=%s, pid=%s, labid=%s"
    logger.info(fmt % (testdate, phone, description, name, email,
                       tempfile.name, sid, pid, labid))
    (hb_userid, hb_password, enabled) = configreader.getCredentials(labid)
    if not enabled:
        logger.info("labid=%s not enabled. Skipping upload", labid)
        return
    savedauth = authmap.get(labid)
    if savedauth is not None:
        (authtoken, savedtime) = savedauth
    if savedauth is None or ((savedauth is not None) and
                             hasThisTimeElapsed(savedtime, hours=24)):
        logger.info("Authenticating for labid=%s", labid)
        try:
            if authmap.get(labid) is not None:
                del authmap[labid]
            authtoken = hbuploader.login(hb_userid, hb_password)
        except:
            logger.error("login method failed for labid=%s" % labid)
            logger.error(traceback.format_exc())
            authtoken = None
            raise Exception("login method failed for labid=%s" % labid)

        if authtoken is None:
            raise Exception("HB Authentication failed for labid=%s" % labid)

        savedtime = datetime.datetime.now()
        authmap[labid] = (authtoken, savedtime)

    success = hbuploader.uploadFile(authtoken, testdate, phone, description,
                                    tempfile.name, sid, pid, name, email)
    if not success:
        raise Exception("HB Upload failure")
    else:
        os.remove(tempfile.name)
        print "Upload for %s (%s) done" % (phone, description)
        logger.info("=========End processing %d  ============" % count)


def callback(ch, method, properties, msg):
    processMsg(msg)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def process():
    print('Attempting contact with rabbitmq. To exit press CTRL+C')
    logger.info('Attempting contact with rabbitmq. To exit press CTRL+C')
    count = 0
    logger.info('Reset count to %d' % count)

    global connection

    credentials = pika.PlainCredentials(url.username, rabbitmq_password)
    params = pika.ConnectionParameters(host=url.hostname,
                                       virtual_host=url.path[1:],
                                       credentials=credentials,
                                       heartbeat_interval=0)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    logger.info("Established connecton with rabbitmq")
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(callback,
                          queue=queue_name)

    print('Connected with rabbitmq. Waiting for reports. To exit press CTRL+C')
    logger.info('Connected with rabbitmq. Waiting for reports. To exit press CTRL+C')

    channel.start_consuming()


parser = argparse.ArgumentParser(description='Upload reports to HB Servers')
parser.add_argument('configfile', help="config file")
args = parser.parse_args()
configreader = ConfigReader(args.configfile)

queue_name = configreader.queue
url_str = configreader.uri
timetowait = configreader.timetowait

url = urlparse.urlparse(url_str)

rabbitmq_password = url.password
if rabbitmq_password is None:
    rabbitmq_password = "guest"

hbuploader = uploader.HBUploader(httpsproxy=configreader.httpsproxy)

while True:
    try:
        authentication = None
        # now enter into regular wait for rabbitmq messages
        process()
    except KeyboardInterrupt:
        logger.error("\nKeyboardInterrupt received: exiting")
        if connection:
            connection.close()
            connection = None
            logger.info("Closed connecton with rabbitmq")
        break
    except pika.exceptions.ConnectionClosed:
        connection = None
        logger.error("Exception: Rabbitmq connection got closed")
        logger.error(traceback.format_exc())
        logger.error("Exception received. Will start again in %d s" %
                     timetowait)
        time.sleep(timetowait)
    except Exception, err:
        logger.error("Generic Exception received")
        logger.error(traceback.format_exc())
        if connection:
            connection.close()
            connection = None
        logger.error("Closed connecton with rabbitmq")
        logger.error(traceback.format_exc())
        logger.error("Exception received. Will start again in %d s" %
                     timetowait)
        time.sleep(timetowait)
