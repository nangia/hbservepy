import pika
import msgpack
import tempfile
import uploader
import argparse



connection = pika.BlockingConnection(pika.ConnectionParameters(
               'localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')

tmpDir = "/Users/sandeep/Documents/vartman/healthbank/hbservepy/tmp"


def getTempFile(dir=tmpDir):
    return tempfile.NamedTemporaryFile(dir=tmpDir,
                                       delete=False, suffix=".pdf")
userid = ""
password = ""


def callback(ch, method, properties, body):
    tuple = msgpack.unpackb(body)
    (testdate, phone, description, name, email, fileblob) = tuple
    tempfile = getTempFile()
    tempfile.write(fileblob)
    tempfile.close()
    print testdate, phone, description, name, email, tempfile.name
    authentication = uploader.login(userid, password)
    retval = uploader.uploadFile(authentication, testdate, phone, description,
                                 tempfile.name)
    print retval


parser = argparse.ArgumentParser(description='Process messages & upload to HB Servers')
parser.add_argument('userid', help='Your userid')
parser.add_argument('password', help='Your password')
args = parser.parse_args()

userid = args.userid
password = args.password

channel.basic_consume(callback,
                      queue='hello',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
