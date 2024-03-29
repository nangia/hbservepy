from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from cgi import parse_header, parse_multipart
from urlparse import parse_qs
import argparse
import tempfile
import re

defaultport = 8000
delibratefalure = False
lastsuccess = False


def validatedatetime(datetimestring):
    if re.match(r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d', datetimestring):
        return True
    return False


# return None if valid
def validatechbserver(testdate, phone, description):
    if testdate is None:
        return "Must provide testdate"
    if not validatedatetime(testdate):
        return "Unexpected date format"
    if phone is None:
        return "Must provide phone"
    if description is None:
        return "Must provide description"
    if description == "":
        return "Cannot have empty description"

    if not (re.match(r'\d+', phone) and len(phone) == 12):
        return "Phone must be 12 digits (only numbers)"

    return None


def gettempfile(dir):
    # file exists need a different name
    tempf = tempfile.NamedTemporaryFile(delete=False, dir=dir, suffix=".pdf")
    tempname = tempf.name
    tempf.close()
    return tempname


class Handler(BaseHTTPRequestHandler):
    def parse_POST(self):
        ctype, pdict = parse_header(self.headers['content-type'])
        if ctype == 'multipart/form-data':
            postvars = parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers['content-length'])
            postvars = parse_qs(
                    self.rfile.read(length),
                    keep_blank_values=1)
        else:
            postvars = {}
        return postvars

    def response_helper(self, thetext, code):
        response = thetext
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-length', len(response))
        self.end_headers()
        print response
        self.wfile.write(response)

    def do_POST(self):
        global lastsuccess
        postvars = self.parse_POST()
        print postvars.keys()
        try:
            testdate = postvars['testdate'][0]
            phone = postvars['phone'][0]
            description = postvars['description'][0]
            name = postvars['name'][0]
            email = postvars['email'][0]
            sid = postvars['sid'][0]
            pid = postvars['pid'][0]
            file = postvars['file']
            labid = postvars['labid'][0]
        except:
            self.response_helper("Must send all params", 400)
            return

        thetempfile = ""
        if file:
            thetempfile = gettempfile(".")
            fout = open(thetempfile, 'wb')
            fout.write(file[0])
            fout.close()

        errmsg = validatechbserver(testdate, phone, description)
        if errmsg:
            self.response_helper(errmsg, 400)
            return
        if delibratefalure:
            if lastsuccess:
                lastsuccess = False
                self.response_helper("Deliberate failure", 500)
                return
            else:
                lastsuccess = True
                # continue normal processing

        print "testdate = %s" % testdate
        print "phone = %s" % phone
        print "description = %s" % description
        print "name = %s" % name
        print "email = %s" % email
        print "sid = %s" % sid
        print "pid = %s" % pid
        print "labid = %s" % labid
        print "File written to %s" % thetempfile
        self.response_helper('ok', 200)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("TestBench for sendreport.dll")
    helpstr = "Port on which to run (default = %d)" % defaultport
    parser.add_argument('--port',
                        type=int,
                        help=helpstr,
                        default=defaultport)
    parser.add_argument('--errors', action='store_true',
                        help="Will deliberately fail 1 in 2 times")

    args = parser.parse_args()
    delibratefalure = args.errors
    if delibratefalure:
        print "Will deliberately fail for otherwise successful requests"
    try:
        server = HTTPServer(('', args.port), Handler)
        print "Server started on port %d" % args.port
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        print "Server exited after keyboard interrupt"
