import json
import logging
import os

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
        self.pt_parser = PlainTextParser(self.KumoObj)

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
        objects.append(self.get_comments(file_choice=choice))
        objects.extend(self.get_plain_text(log=log))

        objects.extend(self.get_images(image_ids=image_ids, get_download_ext=self.client.get_download_ext,
                                       file_choice=choice))

        return objects

    def get_plain_text(self, log):

        log_msg(self, 'Recovering plain text', 'info')
        return self.pt_parser.get_plain_text(log)

    def parse_log(self, c_log, flat_log):
        """ Log flattening not implemented yet"""
        pass

    def parse_snapshot(self, snapshot, flat_log):
        """ Log flattening not implemented yet"""
        pass

    def get_slide_objects(self, log):
        """ Gets objects(only images for now) associated with slide from the log"""

        log_msg(self, 'Retrieving images', 'info')
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

    def create_obj_list(self, objects, type_):
        obj_list = []
        for i, obj in enumerate(objects):
            filename = '{}{}{}'.format(type_, i, obj.extension)
            obj_list.append(self.KumoObj(filename=filename, content=obj.content))
        return obj_list

    def get_images(self, image_ids, get_download_ext, file_choice):
        """
        Retrives images using private API and image_ids
        :param file_choice: gsuite.FileChoice object
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


class PlainTextParser(object):
    def __init__(self, KumoObj):
        self.KumoObj = KumoObj

    def get_plain_text(self, log):
        p = Presentation(log)
        return self.write_output(p)

    def write_output(self, presentation):
        kumo_list = []
        for i, slide in enumerate(presentation.slide_list):
            slide_i = 'slide' + str(i)
            for j, box in enumerate(presentation.slide_dict[slide]):
                if presentation.box_dict[box]['string']:
                    filename = os.path.join(slide_i, 'box{}.txt'.format(j))
                    kumo_list.append(self.make_pt_obj(filename, box, presentation.box_dict))

        return kumo_list

    def make_pt_obj(self, filename, box, box_dict):
        content = box_dict[box]['string'].encode('utf8')
        return self.KumoObj(filename=filename, content=content)


class Presentation(object):
    """ Local representation of GSuite presentation"""

    def __init__(self, log):
        """ Each presentation initializes with the first slide named 'p' containing boxes i0,i1,i3"""
        self.functions = {15: self.add_text, 4: self.parse_mts, 16: self.del_text, 3: self.add_box,
                          12: self.add_slide, 13: self.del_slide, 0: self.del_box, 14: self.move_slide}
        self.slide_dict = {'p': ['i0', 'i1', 'i3']}
        self.box_dict = {'i0': {'slide': 'p', 'string': ''},
                         'i1': {'slide': 'p', 'string': ''},
                         'i3': {'slide': 'p', 'string': ''}}
        self.slide_list = ['p']
        self.data = self.trim_log(log)
        self.parse(self.data)

    def trim_log(self, log):
        """
        :param log: Revision log
        :return: Returns changelog portion of revision log
        """

        return log['changelog'][1:]

    def parse(self, data):
        for entry in data:
            line = entry[0]
            self.parse_line(line)

    def parse_line(self, line):
        action = line[0]
        if action in self.functions:
            func = self.functions[action]
            func(line)

    def add_text(self, line):
        """ Adds a string to a given box at the given index """
        box_dest = line[1]
        add_string = line[4]
        index = line[3]
        old_string = self.box_dict[box_dest]['string']
        new_string = self.insert(old_string, add_string, index)
        self.box_dict[box_dest]['string'] = new_string

    def insert(self, old, add, i):
        """ Returns a new string with the added portion inserted at index i """
        return old[:i] + add + old[i:]

    def delete(self, old, start, end):
        """ Returns a new string with the portion deleted from si to ei """
        return old[:start] + old[end:]

    def parse_mts(self, data):
        """ Parse each line entry separately in the multiset """
        action_list = data[1]
        for line in action_list:
            self.parse_line(line)

    def del_text(self, line):
        """ Deletes the given range from the string at the given box """
        box_dest = line[1]
        start_i, end_i = line[3], line[4]
        old_string = self.box_dict[box_dest]['string']
        new_string = self.delete(old_string, start_i, end_i)
        self.box_dict[box_dest]['string'] = new_string

    def add_box(self, line):
        """ Adds a new box to the collection of boxes"""
        box_attrib = {}
        slide = line[5]
        if slide.endswith(':notes'):
            slide = slide.replace(':notes', '')
        box_id = line[1]
        box_attrib['slide'] = slide
        box_attrib['string'] = ''
        self.box_dict[box_id] = box_attrib

        if slide in self.slide_dict:
            self.slide_dict[slide].append(box_id)
        else:
            self.slide_dict[slide] = [box_id]

    def add_slide(self, line):
        """ Adds a slide and slide id to the collection """
        i = line[2]
        slide_id = line[1]
        self.slide_list.insert(i, slide_id)

        if slide_id not in self.slide_dict:
            self.slide_dict[slide_id] = []

    def del_slide(self, line):
        """ Deletes a slide given the ID and location """
        i = line[1]
        if line[4] == self.slide_list[i]:
            self.slide_list.pop(i)

    def del_box(self, line):
        """ Deletes a box from the given slide """
        for box in line[1]:
            try:
                parent = self.box_dict[box]['slide']
                del self.box_dict[box]
                self.slide_dict[parent].remove(box)
            except KeyError:
                log_msg(cls=self, msg='Error while deleting box {}'.format(box), error_level='exception')

    def move_slide(self, line):
        """ Swap slides at position line[1] and line[2] in slide_list"""
        start_index = line[1]
        end_index = line[2]
        self.slide_list[start_index] = self.slide_list[end_index]
        self.slide_list[end_index] = self.slide_list[start_index]
