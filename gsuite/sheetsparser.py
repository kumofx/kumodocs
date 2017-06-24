import json
import logging

import gsuite

DELIMITER = '|'


# TODO refactor all service requests to gapiclient

# module level functions
def log_msg(cls, msg, error_level):
    """
    Module-level method logs msg with given error_lvl to a logger created with cls name.  
    :param cls: Instance of class object calling the logger
    :param msg: Message to log 
    :param error_level Error level to log message at
    :return: None
    """
    logger = logging.getLogger(cls.__class__.__name__)
    log_func = getattr(logger, error_level)
    log_func(msg)


class SheetsParser(object):
    def __init__(self, client, KumoObj, delimiter='|'):
        self.log = None
        self.flat_log = None
        self.delimiter = delimiter
        self.client = client
        self.service = client.service  # api service
        self.KumoObj = KumoObj

    def get_log(self, start, end, choice):
        log_msg(self, "Retrieving revision log", "info")
        log_url = self.client.create_log_url(start=start, end=end, choice=choice)
        response, log = self.client.request(url=log_url)
        if log.startswith(gsuite.LOG_START_CHR):
            trimmed_log = log[len(gsuite.LOG_START_CHR):]
            return json.loads(trimmed_log)
        else:
            log_msg(self, 'Beginning of log = {}'.format(log[:10]), 'debug')
            raise gsuite.InvalidLogFormat('Check gsuite.LOG_START_CHR and compare to beginning of log')

    def recover_objects(self, log, flat_log):
        """ Recovers plain text, comments, images, drawings, and suggestions from flat_log. 
        :return: A list of recovered objects as KumoObj
        """

        log_obj = self.KumoObj(filename='revision-log.txt', content=json.dumps(log))
        objects = [log_obj]

        return objects

    def parse_log(self, c_log, flat_log):
        pass

    def parse_snapshot(self, snapshot, flat_log):
        pass
