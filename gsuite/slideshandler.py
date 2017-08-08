import logging
import os

from baseclass import Handler, Parser
# noinspection PyUnresolvedReferences
from docshandler import ImageParser, CommentsParser, create_obj_list, insert, delete

# TODO refactor all service requests to gapiclient
INDEX_OFFSET = 0
logger = logging.getLogger(__name__)


class SlidesHandler(Handler):
    @property
    def parsers(self):
        return self._parsers

    @property
    def logger(self):
        return logger

    class SlidesLine(object):
        """ Abstraction of a Slides revision log entry along with methods required to retrieve objects"""

        def __init__(self, line):
            self.line = line

            # indices associated with nested access
            self.mts = [0, 0]
            self.ins = [0, 1, 1, 0]
            self.vid = [0, 1, 0, 4]
            self.url = [0, 1, 0, 4, 11]
            self.not_drive = [0, 1, 0, 4, 9]

        @property
        def image_id(self):
            """ Returns image_id associated with image insertion """
            try:
                image_section = self.line[0][1][0][4]
            except IndexError:
                _image_id = None
            else:
                if self.is_url_src():
                    if self.not_drive_src():
                        id_index = 7  # self.line[0][1][0][4][7]
                    else:
                        id_index = 9  # _image_id = self.line[0][1][0][4][9]
                else:  # uploaded by url, source in [][]..[9], image_id in [11]
                    id_index = 9 if self.has_vid_insert() else 11  # _image_id = self.line[0][1][0][4][11]

                _image_id = image_section[id_index]
            return _image_id

        @property
        def slide_id(self):
            """ Returns slide_id associated with object insertion """
            try:
                _slide_id = self.line[0][1][0][5]
            except IndexError:
                _slide_id = None

            return _slide_id

        def check_nested_value(self, index_list, target, func):
            """
            Accesses a deeply nested item in self.line and compares func(value) to target.  For index_list = [0, 1,
            1, 0] and target = 44, this is equivalent to func(self.line[0][1][1][0]) == 44
            :param index_list: List of indices
            :param target: Value to compare against
            :param func:  Function applied to the result of self.line[][]...[]
            :return: Boolean comparing func(self.line[index_list[0]][index_list[1]]...[index_list[n]]) == target
            """

            try:
                return func(reduce(lambda a, b: a.__getitem__(b), index_list, self.line)) == target
            except:
                return False

        def has_multiset(self):
            return self.check_nested_value(self.mts, 4, int)

        def has_insert_section(self):
            return self.check_nested_value(self.ins, 44, int)

        def has_vid_insert(self):
            return self.check_nested_value(self.vid, 18, len)

        def is_url_src(self):
            return self.check_nested_value(self.url, list, type)

        def not_drive_src(self):
            return self.check_nested_value(self.not_drive, target=list, func=type)

    def __init__(self, client, delimiter=None, parsers=None):
        super(SlidesHandler, self).__init__(client, delimiter)
        self._parsers = [self.init_parser(p) for p in parsers or self.collect_parsers(__name__)]

        self.pt_parser = PlainTextParser(self.KumoObj)

    def parser_opts(self, log, flat_log, choice):
        """ Additional arguments get sent to each parser's parse() function"""

        image_ids = self.get_slide_objects(log)
        return {'image_ids': image_ids}

    def get_slide_objects(self, log):
        """ Gets objects(only images for now) associated with slide from the log"""

        self.logger.info('Retrieving images')
        image_ids = {}

        for line in (self.SlidesLine(entry) for entry in log['changelog']):
            if line.has_multiset() and line.has_insert_section():
                image_ids[line.image_id] = line.slide_id

        return image_ids


class PlainTextParser(Parser):
    """ Returns a list of KumoObj containing plain-text for each text box for each slide"""

    @property
    def logger(self):
        return logger

    def __init__(self, service):
        super(PlainTextParser, self).__init__(service)
        self.KumoObj = SlidesHandler.KumoObj

    def parse(self, log, flat_log, choice, **kwargs):
        """ Returns a list of KumoObj containing plain-text content for each text box in the presentation"""
        self.logger.info('Recovering plain text')
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
        self.logger = logger
        self.data = self.trim_log(log)
        self.parse(self.data)

    @staticmethod
    def trim_log(log):
        """
        :param log: Revision log
        :return: Returns changelog portion of revision log
        """

        return log['changelog'][1:]

    def parse(self, data):
        """
        Sends each line to be parsed
        :param data: Changelog portion of revision log
        :return: None
        """
        for entry in data:
            line = entry[0]
            self.parse_line(line)

    def parse_line(self, line):
        """
        Calls appropriate function based on action type in each line
        :param line: A single entry in the changelog
        :return: None
        """
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
        new_string = insert(old_string, add_string, index, index_offset=INDEX_OFFSET)
        self.box_dict[box_dest]['string'] = new_string

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
        new_string = delete(old_string, start_i, end_i, index_offset=INDEX_OFFSET)
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
                self.logger.exception('Error while deleting box {}'.format(box))

    def move_slide(self, line):
        """ Swap slides at position line[1] and line[2] in slide_list"""
        start_index = line[1]
        end_index = line[2]
        self.slide_list[start_index], self.slide_list[end_index] = self.slide_list[end_index], self.slide_list[
            start_index]
