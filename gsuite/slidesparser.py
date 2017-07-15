import json
import logging

import gsuite
from docsparser import ImageParser, CommentsParser

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


class SlidesParser(object):
    def __init__(self, client, KumoObj, delimiter='|'):
        self.log = None
        self.flat_log = None
        self.delimiter = delimiter
        self.client = client
        self.service = client.service  # api service
        self.KumoObj = KumoObj

        # parsers
        self.image_parser = ImageParser(self.service)
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
        image_ids = self.get_slide_objects(log=log)
        objects.append(self.KumoObj(filename='revision-log.txt', content=json.dumps(log, indent=4)))
        # objects.extend(self.get_plain_text(flat_log=flat_log))
        objects.append(self.get_comments(file_choice=choice))
        objects.extend(self.get_images(image_ids=image_ids, get_download_ext=self.client.get_download_ext,
                                       file_choice=choice))

        return objects

    def parse_log(self, c_log, flat_log):
        """ Log flattening not implemented yet"""
        pass

    def parse_snapshot(self, snapshot, flat_log):
        """ Log flattening not implemented yet"""
        pass

    def get_slide_objects(self, log):
        """ Gets objects(only images for now) associated with slide from the log"""
        image_ids = {}
        for line in log['changelog']:
            # line[0][0] is action type, 4 is multiset, 44 is insert image action
            # for video inserts, len...[4] is 18; exclude video inserts for now
            if line[0][0] == 4 and line[0][1][1][0] == 44 and len(line[0][1][0][4]) != 18:
                # for drive,personal upload, image id in ...[9], else if url in ...[11]
                slide_id = line[0][1][0][5]
                # if ..[11] is a list, the image was not uploaded via url
                if type(line[0][1][0][4][11]) == list:
                    # if ..[9] is a list, not uploaded by drive
                    if type(line[0][1][0][4][9]) == list:
                        image_id = line[0][1][0][4][7]
                    else:
                        image_id = line[0][1][0][4][9]
                else:
                    # if 11 is not a list, it was uploaded by url, src in ...[9]
                    image_id = line[0][1][0][4][11]

                # image_ids[slide_id].append(image_id)
                image_ids[image_id] = slide_id

        return image_ids

    def create_obj_list(self, objects, type):
        obj_list = []
        for i, obj in enumerate(objects):
            filename = '{}{}{}'.format(type, i, obj.extension)
            obj_list.append(self.KumoObj(filename=filename, content=obj.content))
        return obj_list

    def get_images(self, image_ids, get_download_ext, file_choice):
        """
        Retrives images using private API and image_ids
        :param image_ids: Cosmo image IDs retrieved from a Google Docs log
        :param get_download_ext: Function which retrieves the proper image extension
        :return: List of KumoObj with image contents.
        """
        log_msg(self, 'Retrieving images', 'info')
        images = self.image_parser.get_images(image_ids=image_ids, file_id=file_choice.file_id,
                                              drive=file_choice.drive, get_download_ext=get_download_ext)

        return self.create_obj_list(images, 'img')

    def get_comments(self, file_choice):
        """
        Retrieves comment data using GSuite API.
        :return: KumoObj containing retrieved comment data
        """
        log_msg(self, 'Retrieving comments', 'info')
        comments = '\n'.join(str(line) for line in self.comments_parser.get_comments(file_choice.file_id))
        comment_obj = self.KumoObj(filename='comments.txt', content=comments)
        return comment_obj
