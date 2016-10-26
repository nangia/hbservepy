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

    def __init__(self, filename):
        self.config.read(filename)
        logger.info("Read configuration from %s" % filename)

        self.uri = self.config.get('common', 'uri')
        self.queue = self.config.get('common', 'queue')
        self.timetowait = int(self.config.get('common', 'timetowait'))
        logger.info("uri = %s" % self.uri)
        logger.info("queue = %s" % self.queue)
        logger.info("timetowait = %s" % self.timetowait)

        for section in self.config.sections():
            if section != "common":
                self.configstore[section] = (self.config.get(section,
                                                             'username'),
                                             self.config.get(section,
                                                             'password'))
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


if __name__ == "__main__":
    thereader = ConfigReader("processmsg.cfg")
    print thereader.uri
    print thereader.queue
    print thereader.timetowait
    print thereader.configstore

    print "Credentials for lab x ", thereader.getCredentials("x")
    print "Credentials for lab haematology", thereader.getCredentials(
        "heamatology")
