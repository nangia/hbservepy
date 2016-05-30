from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from cgi import parse_header, parse_multipart
from urlparse import parse_qs
import argparse
import tempfile
import re


defaultport = 8000

# TODOs:
# check that testdate is in appropriate date format ISO8601
# check that phone is 12 digits of numbers
# description is not empty


# return None if valid
def validatechbserver(testdate, phone, description):
    if testdate is None:
        return "Must provide testdate"
    # TODO: more check on testdate, phone, description
    if phone is None:
        return "Must provide phone"
    if description is None:
        return "Must provide description"
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

    def do_POST(self):
        postvars = self.parse_POST()
        print postvars.keys()
        testdate = postvars['testdate'][0]
        phone = postvars['phone'][0]
        description = postvars['description'][0]
        file = postvars.get('file')
        thetempfile = ""
        if file:
            thetempfile = gettempfile(".")
            fout = open(thetempfile, 'wb')
            fout.write(file[0])
            fout.close()

        errmsg = validatechbserver(testdate, phone, description)
        if errmsg:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(errmsg)
            return
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        print "testdate = %s" % testdate
        print "phone = %s" % phone
        print "description = %s" % description
        print "File written to %s" % thetempfile
        self.wfile.write('ok')


if __name__ == "__main__":
    parser = argparse.ArgumentParser("TestBench for sendreport.dll")
    helpstr = "Port on which to run (default = %d)" % defaultport
    parser.add_argument('--port',
                        type=int,
                        help=helpstr,
                        default=defaultport)
    args = parser.parse_args()
    try:
        server = HTTPServer(('', args.port), Handler)
        print "Server started on port %d" % args.port
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        print "Server exited after keyboard interrupt"
