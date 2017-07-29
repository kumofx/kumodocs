import json

from gsuite import log_msg
from gsuite.docsparser import CommentsParser

DELIMITER = '|'


# TODO refactor all service requests to gapiclient


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
