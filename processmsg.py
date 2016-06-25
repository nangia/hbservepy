import pika
import msgpack
import tempfile

connection = pika.BlockingConnection(pika.ConnectionParameters(
               'localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')

tmpDir = "/Users/sandeep/Documents/vartman/healthbank/hbservepy/tmp"


def getTempFile(dir=tmpDir):
    return tempfile.NamedTemporaryFile(dir=tmpDir,
                                       delete=False, suffix=".pdf")


def callback(ch, method, properties, body):
    tuple = msgpack.unpackb(body)
    (testdate, phone, description, name, email, fileblob) = tuple
    tempfile = getTempFile()
    tempfile.write(fileblob)
    tempfile.close()
    print testdate, phone, description, name, email, tempfile.name

channel.basic_consume(callback,
                      queue='hello',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
