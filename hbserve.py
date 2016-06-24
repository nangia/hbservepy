import cherrypy
import cgi
import pika
import msgpack

import re
import os
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)

print "localDir = %s" % localDir
print "absDir = %s" % absDir


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
            return "%d %s %s" % (size, file.filename, file.content_type)


hbserveconf = os.path.join(os.path.dirname(__file__), 'hbserve.conf')

if __name__ == '__main__':
    cherrypy.quickstart(HBServe(), config=hbserveconf)
