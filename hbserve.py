import cherrypy
import cgi
import pika
import msgpack

msgpack.packb([1,2,3])
defaultport = 8000

connection = pika.BlockingConnection()
print connection

class HelloWorld(object):
    @cherrypy.expose
    def index(self):
        return "hello world!"
        
 
if __name__ == '__main__':
    cherrypy.quickstart(HelloWorld())