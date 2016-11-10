import logging
from ConfigParser import SafeConfigParser

logger = logging.getLogger()


class ConfigReader(object):
    """
    Be able to read configuration parameters
    """
    uri = "amqp://guest@localhost//"
    queue = "report_queue"
    timetowait = 600
    configstore = {}
    config = SafeConfigParser()
    verify = True

    def __init__(self, filename):
        self.config.read(filename)
        logger.info("Read configuration from %s" % filename)

        self.uri = self.config.get('common', 'uri')
        self.queue = self.config.get('common', 'queue')
        self.timetowait = int(self.config.get('common', 'timetowait'))
        logger.info("uri = %s" % self.uri)
        logger.info("queue = %s" % self.queue)
        logger.info("timetowait = %s" % self.timetowait)
        if self.config.has_option('common', 'httpsproxy'):
            self.httpsproxy = self.config.get('common', 'httpsproxy')
        else:
            self.httpsproxy = None
        logger.info("httpsproxy = %s" % self.httpsproxy)
        if self.config.has_option('common', 'verify'):
            verify = self.config.get('common', 'verify')
            if type(verify) == str and verify.upper() == "FALSE":
                self.verify = False
            elif type(verify) == str and verify.upper() == "TRUE":
                self.verify = True
            else:
                self.verify = verify

        for section in self.config.sections():
            if section != "common":
                self.configstore[section] = (
                    self.config.get(section, 'username'),
                    self.config.get(section, 'password'),
                    self.config.getboolean(section, 'enabled')
                )
        logger.info("Stored info for %s section" %
                    ",".join(self.config.sections()))

    def getCredentials(self, labid):
        tuple = self.configstore.get(labid)
        if tuple is None:
            logger.info("No credentials for labid=%s. Using fallback" %
                        labid)
            return self.configstore.get("fallback")
        else:
            return tuple

    def getProxies(self):
        if self.httpsproxy:
            return {'https': self.httpsproxy}
        else:
            return None

if __name__ == "__main__":
    thereader = ConfigReader("processmsg.cfg")
    print thereader.uri
    print thereader.queue
    print thereader.timetowait
    print thereader.configstore

    print "Credentials for lab x ", thereader.getCredentials("x")
    print "Credentials for lab haematology", thereader.getCredentials(
        "heamatology")
