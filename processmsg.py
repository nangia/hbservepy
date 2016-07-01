import pika
import msgpack
import tempfile
import uploader
import argparse
import urlparse
import time
import traceback
import os



hb_userid = ""
hb_password = ""
rabbitmq_password = ""
url_str = "amqp://guest@localhost//"
queue_name = "report_queue"
tmpDirName = "tmp"
tmpDir = "tmp"
count = 0


def getTempFile(dir):
    return tempfile.NamedTemporaryFile(dir=tmpDir,
                                       delete=False, suffix=".pdf")


def processMsg(msg):
    global count
    count = count + 1
    print "========Starting processing %d =========" % count
    tuple = msgpack.unpackb(msg)
    (testdate, phone, description, name, email, fileblob) = tuple
    print "processMsg: processing %s for %s" % (description, phone)
    tempfile = getTempFile(tmpDirName)
    tempfile.write(fileblob)
    tempfile.close()
    print testdate, phone, description, name, email, tempfile.name
    authentication = uploader.login(hb_userid, hb_password)
    if authentication is None:
        raise Exception("HB Authentication failed")
    success = uploader.uploadFile(authentication, testdate, phone, description,
                                  tempfile.name)
    if not success:
        raise Exception("HB Upload failure")
    else:
        os.remove(tempfile.name)
        print "=========End processing %d ============" % count


def callback(ch, method, properties, msg):
    processMsg(msg)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def process():
    credentials = pika.PlainCredentials(url.username, rabbitmq_password)
    params = pika.ConnectionParameters(host=url.hostname,
                                       virtual_host=url.path[1:],
                                       credentials=credentials)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(callback,
                          queue=queue_name)

    channel.start_consuming()


if __name__ == '__main__':
    executablename = os.path.realpath(__file__)
    dirname = os.path.dirname(executablename)
    tmpDir = os.path.join(dirname, tmpDirName)
    print "tmpDir = %s" % tmpDir
    if not os.path.isdir(tmpDir) or not os.path.exists(tmpDir):
        print "%s does not exist. Exiting" % tmpDir
        exit(-1)
    parser = argparse.ArgumentParser(description='Process messages & upload to HB Servers')
    parser.add_argument('userid', help='Your HB userid')
    parser.add_argument('password', help='Your HB password')
    parser.add_argument('--uri',
                        help="URI for AMQP queue",
                        default=url_str)
    parser.add_argument('--queue',
                        help="Queue name in AMQP queue",
                        default=queue_name)

    args = parser.parse_args()
    queue_name = args.queue
    hb_userid = args.userid
    hb_password = args.password

    url_str = args.uri
    url = urlparse.urlparse(url_str)

    rabbitmq_password = url.password
    if rabbitmq_password is None:
        rabbitmq_password = "guest"
    timetowait = 5
    while True:
        try:
            # now enter into regular wait for rabbitmq messages
            print(' [*] Waiting for messages. To exit press CTRL+C')

            process()
        except KeyboardInterrupt:
            print "\nKeyboardInterrupt received: exiting"
            break
        except Exception, err:
            print traceback.format_exc()
            print "Exception received. Starting again in %d s" % timetowait
            time.sleep(timetowait)
            timetowait = 2 * timetowait



# logging
# TODO: what if login fails


# TOOD: print what kind of exception and log it

# TODO: what if internet fails

# infinite loop that keeps starting over in case of exceptions

# In case a login failure, upload failure or exception occurs after retrieving
# a key from rabbitmq, it is not uploaded at all


# don't login repeatedly unnecessarily - perhaps login at the start of loop (which gets reiniaited after exception)


# version numbers to be done appropriately
