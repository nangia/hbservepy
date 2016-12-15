hbservepy 
=======================
hbservepy illustrates how to get medical labs to enable them to put their medical reports on health bank platform.

To summarize, the reports along with specific parameters for the patients need to be posted to a webserver which will then queue it up and then upload to health bank servers. The parameters to be posted to this URL are: file, testdate, phone (12 digit number), description,  name (of patient), email (of patient), sid (unique test id), pid (patient id), labid (lab id - as within a setup there might be multiple ids).

The software consists of 4 components:

1. *hbserve.py*: A lightweight browser which accepts medical reports via a simple http POST. After receiving these reports, it queues them up in a Rabbitmq queue.
2. *processmsg.py*: A process that listens to messages coming onto Rabbitmq queue which uploads them to health bank servers.
3. *testbench.py*: A process that can be used during development instead of using hbserve.py and processmsg.py. This just prints the parameters coming in (and saves the incoming file) instead of doing the actual uploads.
4. *hbheartbeat.py*: A process that can be optionally run. This is to check periodically whether the internet connection is operational from the lab. When enabled at the server end, the lab owner can be pinged via email if the connection goes down.

Of course, you need to run a valid RabbitMQ instance against which *hbserve.py* will queue up requets and *processmsg.py* will retrieve them and then upload to health bank servers.

Configuration Files
===============
Example hbserve.conf
------
```
[global]
server.thread_pool: 1
server.socket_port: 9090
log.screen: True
log.access_file: "/Users/healthbank/Documents/vartman/healthbank/hbservepy/cherry.log"
log.error_file: "/Users/healthbank/Documents/vartman/healthbank/hbservepy/cherry.log"
```

Example processmsg.cfg
----
```
[common]
timetowait=600 # time to wait before starting process loop again in case an error happens
uri=amqp://guest@localhost//  # Rabbitmq URL
queue=report_queue  # queue name for Rabbitmq
# baseurl=https://www.healthbankapp.com/api/v1/  # you should never have to change this. There for debugging purposes
#verify=false # uncomment this to turn off SSL verification. Not recommended. 
# verify=fullchain.pem # uncomment and provide certificate just in case you are using old python and can't update certificates
# ucomment the following line if you want communication via proxy 
#httpsproxy=127.0.0.1:8080 

[fallback]
# credentials for fallback lab userid
username=919999999999
password=password
enabled=true
[haematology]
# specify credentials for each lab
username=918888888888
password=password
enabled=true
````