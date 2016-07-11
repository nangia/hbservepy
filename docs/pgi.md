Interface Document for Sending Reports to Mobile
----------

Purpose of this Document
==========

The purpose of this document is to describe the mechanism how medical reports will be made available to patients on their mobiles.

Figure 1(a) shows how the reports need to flow from the laboratory software to the Intermediary to Cloud Server which will then make it available to the mobile devices.

Figure 1(b) explains how this will be accomplished. The reports will flow from the laboratory software to a DLL (called CloudInterface) which will then transmit to intermediary software (Interface to Cloud Server) which will then transmit it to Cloud server from where reports are available to the mobile devices.

![Figure 1](/Users/sandeep/Documents/vartman/healthbank/hbservepy/docs/diag4.png)

For development and modification purposes of the Laboratory software, we need a test bench so that independent testing can be done on the modifications of the laboratory sofware without dependence on the many components that are there in Figure 1(b). This is accomplished using testbench.exe as illustrated in Figure 1(c).  With that the Laboratory software changes can be tested.


The interface to Cloud server is nothing but a light weight http server to which reports along with data need to be POSTed so that further processing can be done.

Requirements for the Software at the Lab
===========

All that is needed from the software at the lab is to call CloudInterface by POSTing the data to the webserver provided.

This can be done through following mechanisms:

* Use a C library called sendreport.dll (The details are not provided here.) In case you wish you use the C interface, please contact sandeep@healthbankapp.com.
* Directly POST to the http server. A java example is also provided on how this can be done. This is what this document details. Permisson is hereby granted to use this example code.

Thus when the report is ready to be made available to patient the software will use one of the mechanisms above with the pdf of the report file which will then be transmitted to the patient by the interface to the cloud server.



How to run testbench.exe and test against that
=============

To make the development easier a Test Bench is provided (called testbench.exe). Instead of providing full functionality and transmitting to the cloud servers, the testbench.exe just prints what is POSTed to it. It also saves the POSTed PDF file so that it can checked if the transmission was successful.

Please see instructions below on how to run it:

* On the development machine (or a separate machine), let's call this machine X, run ```testbench.exe``` by running ```testbench.exe``` on the Windows command line.
* Now POST the data to this server X using any program (a Java example is provided). 
* As each report is given to ```testbench.exe``` one can also see the corresponding data that is transmitted to it for debugging purposes. Also the PDF file is saved at a temporary location. 
* Note that you can run ```testbench.exe --errors``` to delibrately send errors 1 in 2 times. This is so that one can test that the sender of the reports should try to send reports again.

Description of Components
===========

testproj
----------
This is a sample Java program that shows how to POST report data to testbench.exe or CloudInterface.

testbench.exe
---------
This testbench.exe is to be run so that testing can be done.

You can run testbench.exe on the same computer or a different one (note you have to provide the URL to this computer accordingly). By default testbench.exe makes its services available on port 8000 but one can choose a different port by running 

```testbench.exe --port 8800```

Also there is an option available so that deliberate errors are send back by testbench.exe for alternative invocations. This is there so that the scenario that if an error occurs, the transmission of that particular medical report should be retried again.

```testbench.exe --errors```

To see all the options, use the following command:

```testbench.exe -h```

Details of sendreport function in sample project
====================
    public static void sendreport(String url, String filepath, 
    	String testdate, String phone, String description, String patient_name,
    	String patient_email, String test_unique_id, 
    	String patient_unique_id) throws Exception 
----------

The sendreport function gives an example how various paramters are to be transmitted to testbench.exe. Please go through the code on how this is accomplished. The paramters are documented below:

Parameters:

- url: The URL where testbench.exe is running. Note that this URL is to be picked from configuration parameters and must not be hardcoded. Note that this must correspond to the place where testbench.exe must be running. So if testbench.exe is running on IP addres 10.0.2.15 on port 8000, the URL should be http://10.0.2.15:8000/
- filepath: the path to the PDF file which contains the report. The file must exist else errors will result.
- testdate: Example string 2016-05-26T05:50 (which means that this test was done at 05:50 am of 26-may-2016). Time is expected to be in UTC. This is the date and time when the test sample was collected.
- phone: A string comprising 12 digits of mobile number of patient i.e. the number +91-9876147766 will be sent as 919876147766. 
- description: some details about the report. e.g. type of tests done. Note this must be brief (<= 30 characters). So what is typically sent when SMS are sent can be used here. Or you may send the laboratory desription.
- patient_name: Name of patient. If not available, please send "".
- patient_email: email of patient if it is available. If not available, send "". 
- test_unique_id: the unique id of the test that has been conducted against which this report is generated.
- patient_unique_id: the unique atient id of the report. This will be CR number in case of PGI.

Return Value:

There is no return value (void). If there is no Exception the execution was successful. 

Important Note
============

1. In case, if the reports are not successfully submitted to cloud interface, the reports submission must be retried after some time. 

2. Note that instead of using the sample java program for providing reports, one can also directly post the data to the testbench.exe. The paramters should be encoded via ```multipart/form-data```. The paramters and the values are given below. These should be posted to the URL that testbench.exe shows upon being run.

- testdate: Example string 2016-05-26T05:50 (which means that this test was done at 05:50 am of 26-may-2016). Time is expected to be in UTC. This is the date and time when the test sample was collected.
- phone: A string comprising 12 digits of mobile number of patient i.e. the number +91-9876147766 will be sent as 919876147766. 
- description: some details about the report. e.g. type of tests done. Note this must be brief (<= 30 characters). So what is typically sent when SMS are sent can be used here. Or you may send the laboratory desription.
- name: Name of patient. If not available, please send "".
- email: email of patient if it is available. If not available, send "". 
- file: the path to the PDF file which contains the report. The file must exist else errors will result.
- sid: the unique id of the test that has been conducted against which this report is generated.
- pid: the unique atient id of the report. This will be CR number in case of PGI.



Depedencies of Sample Java program
==========================

The sample java program depends on the following components available in Maven repository:

* org.apache.httpcomponents:httpclient:4.5.2 (URL is https://mvnrepository.com/artifact/org.apache.httpcomponents/httpclient/4.5.2])
* org.apache.httpcomponents:httpmime:4.5.2 (URL is https://mvnrepository.com/artifact/org.apache.httpcomponents/httpmime/4.5.2)

In case you decide to use the sample java program, please make sure the dependencies are in the class path.




