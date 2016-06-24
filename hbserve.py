import cherrypy
import cgi
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

hbserveconf = os.path.join(os.path.dirname(__file__), 'hbserve.conf')
bgtask = BackgroundTaskQueue(cherrypy.engine)
bgtask.subscribe()


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

        size = 0
        while True:
            data = file.file.read(8192)
            if not data:
                break
            size += len(data)
        bgtask.put(testlog, "hbserve called")

        return "%d %s %s" % (size, file.filename, file.content_type)


if __name__ == '__main__':
    cherrypy.quickstart(HBServe(), config=hbserveconf)
