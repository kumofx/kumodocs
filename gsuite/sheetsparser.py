import json
import logging

import gsuite
from gsuite.docsparser import CommentsParser

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
    def __init__(self, client, kumo_obj, delimiter='|'):
        self.log = None
        self.flat_log = None
        self.delimiter = delimiter
        self.client = client
        self.service = client.service  # api service
        self.KumoObj = kumo_obj

        # parsers
        self.comments_parser = CommentsParser(self.service)

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

    def recover_objects(self, log, flat_log, choice):
        """ Recovers plain text, comments, images, drawings, and suggestions from flat_log. 
        :return: A list of recovered objects as KumoObj
        """
        objects = []

        if flat_log:
            objects.extend([self.KumoObj(filename='flat-log.txt', content='\n'.join(str(line) for line in flat_log))])
        objects.extend([self.KumoObj(filename='revision-log.txt', content=json.dumps(log, indent=2))])
        objects.extend([self.get_comments(file_choice=choice)])
        return objects

    def get_comments(self, file_choice):
        """
        Retrieves comment data using GSuite API.
        :return: KumoObj containing retrieved comment data
        """
        log_msg(self, 'Retrieving comments', 'info')
        comments = '\n'.join(str(line) for line in self.comments_parser.get_comments(file_choice.file_id))
        comment_obj = self.KumoObj(filename='comments.txt', content=comments)
        return comment_obj

    def parse_log(self, c_log):
        """ Log flattening not implemented yet"""
        return []

    def parse_snapshot(self, snapshot):
        """ Log flattening not implemented yet"""
        return []
