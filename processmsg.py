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


def logging_info(x):
    print x


def logging_error(x):
    print x


def logging_warn(x):
    print x


hb_userid = ""
hb_password = ""
rabbitmq_password = ""
url_str = "amqp://guest@localhost//"
queue_name = "report_queue"
tmpDirName = "tmp"
tmpDir = "tmp"
count = 0

authentication = None
savedtime = None
connection = None


def hasThisTimeElapsed(fromtime, hours=24):
    if fromtime is None:
        return True
    nowtime = datetime.datetime.now()
    delta = datetime.timedelta(hours=hours)
    if nowtime > fromtime + delta:
        return True
    return False


def getTempFile(dir):
    return tempfile.NamedTemporaryFile(dir=tmpDir,
                                       delete=False, suffix=".pdf")


def processMsg(msg):
    global authentication
    global count
    global savedtime
    count = count + 1
    logging_info("========Starting processing %d =========" % count)
    tuple = msgpack.unpackb(msg)
    (testdate, phone, description, name, email, fileblob) = tuple
    logging_info("processMsg: processing %s for %s" % (description, phone))
    tempfile = getTempFile(tmpDirName)
    tempfile.write(fileblob)
    tempfile.close()
    fmt = "testdate=%s phone=%s description=%s name=%s email=%s file=%s"
    logging_info(fmt % (testdate, phone, description, name, email, tempfile.name))
    if authentication is None or ((authentication is not None) and
                                  hasThisTimeElapsed(savedtime, hours=24)):
        logging_info("Authenticating")
        print "Authenticating"
        try:
            authentication = uploader.login(hb_userid, hb_password)
        except:
            logging_error("Authentication failed")
            raise Exception("HB Authentication failed")

        savedtime = datetime.datetime.now()

    success = uploader.uploadFile(authentication, testdate, phone, description,
                                  tempfile.name)
    if not success:
        raise Exception("HB Upload failure")
    else:
        os.remove(tempfile.name)
        logging_info("=========End processing %d ============" % count)


def callback(ch, method, properties, msg):
    processMsg(msg)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def process():
    global connection
    credentials = pika.PlainCredentials(url.username, rabbitmq_password)
    params = pika.ConnectionParameters(host=url.hostname,
                                       virtual_host=url.path[1:],
                                       credentials=credentials)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    print "Established connecton with rabbitmq"
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(callback,
                          queue=queue_name)

    channel.start_consuming()


if __name__ == '__main__':
    executablename = os.path.realpath(__file__)
    dirname = os.path.dirname(executablename)
    tmpDir = os.path.join(dirname, tmpDirName)
    logging_info("tmpDir = %s" % tmpDir)
    if not os.path.isdir(tmpDir) or not os.path.exists(tmpDir):
        logging_error("%s does not exist. Exiting" % tmpDir)
        exit(-1)
    logfile = os.path.join(dirname, "processmsg.log")

    parser = argparse.ArgumentParser(description='Process messages & upload to HB Servers')
    parser.add_argument('userid', help='Your HB userid')
    parser.add_argument('password', help='Your HB password')
    parser.add_argument('--uri',
                        help="URI for AMQP queue",
                        default=url_str)
    parser.add_argument('--queue',
                        help="Queue name in AMQP queue",
                        default=queue_name)
    parser.add_argument('--log',
                        help="Queue name in AMQP queue",
                        default=queue_name)

    args = parser.parse_args()
    queue_name = args.queue
    hb_userid = args.userid
    hb_password = args.password
    loglevel = args.log

    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    print "loglevel (%s) = %d" % (loglevel, numeric_level)
    logging.basicConfig(filename=logfile, level=numeric_level,
                        format='%(asctime)s %(message)s')

    url_str = args.uri
    url = urlparse.urlparse(url_str)

    rabbitmq_password = url.password
    if rabbitmq_password is None:
        rabbitmq_password = "guest"
    timetowait = 10 * 60  # 10 minutes
    while True:
        try:
            authentication = None
            # now enter into regular wait for rabbitmq messages
            print('[*] Waiting for messages. To exit press CTRL+C')
            logging_info('[*] Waiting for messages. To exit press CTRL+C')

            process()
        except KeyboardInterrupt:
            connection.close()
            print "Closed connecton with rabbitmq"
            logging_info("\nKeyboardInterrupt received: exiting")
            break
        except Exception, err:
            connection.close()
            print "Closed connecton with rabbitmq"
            logging_error(traceback.format_exc())
            logging_error("Exception received. Will start again in %d s" % timetowait)
            time.sleep(timetowait)


# TODO: logging

# TODO: what if internet fails

# version numbers to be done appropriately
