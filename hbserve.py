import cherrypy
import pika
import msgpack
import Queue
import threading
from cherrypy.process.plugins import SimplePlugin
import time
import urlparse
import argparse

import re
import os
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)
tmpDir = os.path.join(absDir, "tmp")

cherrypy.log("localDir = %s" % localDir)
cherrypy.log("absDir = %s" % absDir)


def testlog(arg1):
    time.sleep(5)
    cherrypy.log("Got arg1 in testlog")


class BackgroundTaskQueue(SimplePlugin):

    thread = None

    def __init__(self, bus, qsize=100, qwait=2, safe_stop=True):
        SimplePlugin.__init__(self, bus)
        self.q = Queue.Queue(qsize)
        self.qwait = qwait
        self.safe_stop = safe_stop

    def start(self):
        self.running = True
        if not self.thread:
            self.thread = threading.Thread(target=self.run)
            self.thread.start()

    def stop(self):
        if self.safe_stop:
            self.running = "draining"
        else:
            self.running = False

        if self.thread:
            self.thread.join()
            self.thread = None
        self.running = False

    def run(self):
        while self.running:
            try:
                try:
                    func, args, kwargs = self.q.get(block=True, timeout=self.qwait)
                except Queue.Empty:
                    if self.running == "draining":
                        return
                    continue
                else:
                    func(*args, **kwargs)
                    if hasattr(self.q, 'task_done'):
                        self.q.task_done()
            except:
                self.bus.log("Error in BackgroundTaskQueue %r." % self,
                             level=40, traceback=True)

    def put(self, func, *args, **kwargs):
        """Schedule the given func to be run."""
        self.q.put((func, args, kwargs))


def validatedatetime(datetimestring):
    if re.match(r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d', datetimestring):
        return True
    return False


# return None if valid
def validatechbserver(testdate, phone, description):
    if testdate == "":
        return "Must provide testdate"
    if not validatedatetime(testdate):
        return "Unexpected date format"
    if phone == "":
        return "Must provide phone"
    if description == "":
        return "Must provide description"
    if description == "":
        return "Cannot have empty description"

    if not (re.match(r'\d+', phone) and len(phone) == 12):
        return "Phone must be 12 digits (only numbers)"

    return None

hbserveconf = os.path.join(absDir, 'hbserve.conf')
bgtask = BackgroundTaskQueue(cherrypy.engine)
bgtask.subscribe()


connection = None
channel = None

# url_str = "amqp://pkltrust:pkltrust1234@localhost/pkltrust/"
url_str = "amqp://guest@localhost//"
queue_name = "report_queue"


def setup_queue():
    global connection
    global url_str
    global queue
    global channel
    url = urlparse.urlparse(url_str)
    password = url.password

    if password is None:
        password = "guest"
    credentials = pika.PlainCredentials(url.username, password)

    params = pika.ConnectionParameters(host=url.hostname,
                                       virtual_host=url.path[1:],
                                       credentials=credentials)

    # params = pika.ConnectionParameters()
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    # don't hand off more than one message
    channel.basic_qos(prefetch_count=1)
    cherrypy.log("Connection to rabbitmq setup")


def cleanup_queue():
    global connection
    global channel

    connection.close()
    cherrypy.log("Connection to rabbitmq closed")


def pushToQueue(testdate, phone, description, name, email, fileblob):
    packed = msgpack.packb((testdate, phone, description, name, email,
                            fileblob))
    channel.basic_publish(exchange='',
                          routing_key=queue,
                          body=packed,
                          properties=pika.BasicProperties(
                              delivery_mode=2,  # make message persistent
                          ))


class HBServe(object):

    @cherrypy.expose
    def enqueue(self, file, testdate="", phone="", description="",
                name="", email=""):
        cherrypy.log("testdate=%s" % testdate)
        cherrypy.log("phone=%s" % phone)
        cherrypy.log("description=%s" % description)
        cherrypy.log("name=%s" % name)
        cherrypy.log("email=%s" % email)
        err = validatechbserver(testdate, phone, description)
        if err is not None:
            cherrypy.log("Returning 400: err=%s" % err)
            cherrypy.response.status = 400
            return err

        try:
            # bgtask.put(testlog, "hbserve called")
            pushToQueue(testdate, phone, description, name, email,
                        file.file.read())
        except:
            cherrypy.response.status = 400
            return "Unable to enqueue"

        return "ok"


if __name__ == '__main__':
    parser = argparse.ArgumentParser("HBServe: Intermediary for Health Bank")
    parser.add_argument('--uri',
                        help="URI for AMQP queue",
                        default=url_str)
    parser.add_argument('--queue',
                        help="Queue name in AMQP queue",
                        default=queue_name)

    args = parser.parse_args()
    url_str = args.uri
    queue = args.queue
    cherrypy.engine.subscribe('start', setup_queue)
    cherrypy.engine.subscribe('exit', cleanup_queue)

    cherrypy.quickstart(HBServe(), config=hbserveconf)



# TODO: temp directory needs to be auto picked or exit if it does not exist
# TODO: check that the tmp directory must exist



# TODO: handle if pika connections are lost. connect again for hbserver

# TODO: in case auto load is on, print a warning

# TODO: same for client
# TODO: put command line parameters to control configuration (refine it)



# infinite loop that keeps starting over in case of exceptions

# TODO: include requests to be installed. check if version same on windows. otherwise upgrade

# remove old pdf files after sending them successfully

