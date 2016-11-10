import requests
import logging

logger = logging.getLogger()


class HBUploader:
    baseurl = "https://www.healthbankapp.com/api/v1/"
    uploadurlinfo = baseurl + "uploadurlinfo/"
    reportuploadurl = baseurl + "reports/"
    heartbeaturl = baseurl + "heartbeat/"
    loginurl = baseurl + "rest-auth/login/"

    def __init__(self, httpsproxy=None, timeout=30, verify=True):
        if httpsproxy:
            self.proxies = {'https': httpsproxy}
        else:
            self.proxies = None
        self.timeout = timeout  # in seconds
        self.verify = verify

    def login(self, userid, password):
        logger.info("Trying to login")
        params = {
            "username": userid,
            "password": password
        }
        r = requests.post(self.loginurl, data=params, timeout=self.timeout,
                          proxies=self.proxies, verify=self.verify)
        if r.status_code != 200:
            logger.error("Unable to login. Status=%d" % r.status_code)
            return None
        authentication = r.json()['key']
        return authentication

    def uploadFile(self, authentication, testdate, phone, description, thefile,
                   sid, pid, name, email):
        logger.info("Trying to uploadFile")
        headers = {'Authorization': "Token %s" % authentication}

        listoffiles = [thefile]
        params = {}  # empty dictionary
        params['file'] = listoffiles

        # send a get with file having a list of files
        r = requests.get(self.uploadurlinfo, params=params, headers=headers,
                         timeout=self.timeout, proxies=self.proxies,
                         verify=self.verify)
        logger.debug("Status code for /uploadurlinfo/ is %d" % r.status_code)

        if r.status_code != 200:
            logger.error("uploadFile: Exiting as status code is not 200")
            return False

        result = r.json()
        listofuploadinfo = result['uploadurlinfo']

        thelistofs3keys = []
        for uploadinfo in listofuploadinfo:
            url = uploadinfo['url']
            file = uploadinfo['file']
            key = uploadinfo['key']
            thelistofs3keys.append(key)
            # remove these keys url and file from map as these are
            # not to be sent as parameters
            uploadinfo.pop('url', None)
            uploadinfo.pop('file', None)
            logger.debug("Now uploading file %s as %s to %s" % (file,
                                                                key, url))

            # uploadinfo now has all the parameters to be posted.
            # Not needed parameters url and file are removed from the dic
            # Now upload to S3
            files = {'file': open(file, 'rb')}
            r = requests.post(url, data=uploadinfo, files=files,
                              timeout=self.timeout, proxies=self.proxies,
                              verify=self.verify)
            logger.debug("upload status from S3 = %d" % r.status_code)
            if r.status_code != 204:
                logger.error("uploadFile: Exiting as status code from S3 is not 204")
                return False

            # now make a call to /reports
            params = {
                "dateofreport": testdate,
                "description": description,
                "reports3keys": thelistofs3keys,
                "username": phone,
                "sid": sid,
                "pid": pid,
                "name": name,
                "email": email,
            }
            logger.debug("params = %r" % str(params))
            r = requests.post(self.reportuploadurl, data=params,
                              headers=headers, timeout=self.timeout,
                              proxies=self.proxies, verify=self.verify)
            logger.debug("upload status from post to /reports = %d" %
                         r.status_code)
            logger.debug("Return value = %s" % r.text)
            if r.status_code == 202:
                return True
            logger.error("uploadFile: failure")
            jsonval = r.json()
            if 'Invalid phone' in jsonval.get('username'):
                # irrecoverable error
                # just log it and go forward
                logger.error("Invalid phone=%s, sid = %s, pid = %s. Unable to upload" %
                             (phone, sid, pid))
                # this is invalid phone so we can't do anything
                # say a lie that you have processed it successfully so that you get next report
                return True
            return False

    def heartbeat(self, authentication):
        params = {}
        headers = {'Authorization': "Token %s" % authentication}
        r = requests.get(self.heartbeaturl, data=params, headers=headers,
                         timeout=self.timeout, proxies=self.proxies,
                         verify=self.verify)
        logger.debug("Output from heartbeat = %d" % r.status_code)
        logger.debug("Return value = %s" % r.text)
        if r.status_code == 200:
            return True
        return False
