import requests

heroku = True

if heroku:
    baseurl = "https://hbank.herokuapp.com/api/v1/"
else:
    baseurl = "http://localhost:8000/api/v1/"


def login(userid, password):
    loginurl = baseurl + "rest-auth/login/"
    print "Trying to login"
    params = {
        "username": userid,
        "password": password
    }
    r = requests.post(loginurl, data=params)

    if r.status_code != 200:
        print "Unable to login. Status=%d" % r.status_code
        return None
    authentication = r.json()['key']
    return authentication


uploadurlinfo = baseurl + "uploadurlinfo/"
reportupload = baseurl + "reports/"


def uploadFile(authentication, testdate, phone, description, thefile):
    print "Trying to uploadFile"
    headers = {'Authorization': "Token %s" % authentication}

    listoffiles = [thefile]
    params = {}  # empty dictionary
    params['file'] = listoffiles

    # send a get with file having a list of files
    r = requests.get(uploadurlinfo, params=params, headers=headers)

    # print "Status code for /uploadurlinfo/ is %d" % r.status_code

    if r.status_code != 200:
        print "Exiting as status code is not 200"
        return False

    result = r.json()
    listofuploadinfo = result['uploadurlinfo']

    thelistofs3keys = []
    for uploadinfo in listofuploadinfo:
        url = uploadinfo['url']
        file = uploadinfo['file']
        key = uploadinfo['key']
        thelistofs3keys.append(key)
        # remove these keys url and file from map as these are not to be sent
        # as parameters
        uploadinfo.pop('url', None)
        uploadinfo.pop('file', None)
        # print "Now uploading file %s as %s to %s" % (file, key, url)

        # uploadinfo now has all the parameters to be posted.
        # Not needed parameters url and file are removed from the dictionary
        # Now upload to S3
        files = {'file': open(file, 'rb')}
        r = requests.post(url, data=uploadinfo, files=files)
        print "upload status from S3 = %d" % r.status_code
        if r.status_code != 204:
            print "Exiting as status code is not 204"
            return False

        # now make a call to /reports
        params = {
            "dateofreport": testdate,
            "description": description,
            "reports3keys": thelistofs3keys,
            "username": phone,
        }
        # print "params = %s" % str(params)
        r = requests.post(reportupload, data=params, headers=headers)
        # print "upload status from S3 = %d" % r.status_code
        # print r.text
        # print "========================="
        if r.status_code == 202:
            return True
        print "uploadFile: failure"
        return False