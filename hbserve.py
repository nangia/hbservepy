import cherrypy
import pika
import msgpack
import Queue
import threading
from cherrypy.process.plugins import SimplePlugin
import time

import re
import os
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)
tmpDir = os.path.join(absDir, "tmp")

print "localDir = %s" % localDir
print "absDir = %s" % absDir


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


def setup_queue():
    global connection
    global channel
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    print connection
    channel = connection.channel()
    print "channel = %r" % channel
    channel.queue_declare(queue='hello')
    print "Connection to rabbitmq setup"


def cleanup_queue():
    global connection
    global channel

    connection.close()
    print "Connection to rabbitmq closed"


cherrypy.engine.subscribe('start', setup_queue)
cherrypy.engine.subscribe('exit', setup_queue)


def pushToQueue(testdate, phone, description, name, email, fileblob):
    packed = msgpack.packb((testdate, phone, description, name, email,
                            fileblob))
    channel.basic_publish(exchange='',
                          routing_key='hello',
                          body=packed)
    print(" [x] Sent 'Hello World!'")


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
            cherrypy.response.status = 400
            return err

        # bgtask.put(testlog, "hbserve called")
        pushToQueue(testdate, phone, description, name, email,
                    file.file.read())

        # TODO: check what testbench returns
        return "ok"


if __name__ == '__main__':
    # TODO: check that the tmp directory must exist
    # TODO: in case auto load is on, print a warning
    # TODO: rabbitmq should be configurable
    # TODO: send files across rabbitmq

    cherrypy.quickstart(HBServe(), config=hbserveconf)
