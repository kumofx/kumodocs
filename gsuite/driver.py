import logging
import os
from collections import namedtuple

import KIOutils
import basedriver
import gapiclient
import gsuite


class GSuiteDriver(basedriver.BaseDriver):
    """ 
    Functionality to retrieve and flattens Google Docs logs, and recover plain-text, suggestions, comments, 
    and images from the log.
    """

    SuggestionContent = namedtuple('content', 'added, deleted')

    def __init__(self, base_dir='downloaded', delimiter='|'):
        self.client = gapiclient.Client(service='drive', scope='https://www.googleapis.com/auth/drive')
        self._logger = logging.getLogger(__name__)
        self._base_dir = base_dir
        self.delimiter = delimiter
        self.choice = None
        self._parser = None
        self.choice_start = None
        self.choice_end = None

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, value):
        self._logger = value

    @property
    def base_dir(self):
        return self._base_dir

    @base_dir.setter
    def base_dir(self, value):
        self._base_dir = value

    @property
    def parser(self):
        return self._parser

    @parser.setter
    def parser(self, value):
        self._parser = value

    def choose_file(self):
        """
        Presents the user with a virtualized interface of their GSuite contents to choose a file.   
        :return: A namedtuple containing file_id, title, drive, and max_revs
        """
        self.choice = self.client.choose_file()

        if self.choice.drive == 'document':
            from docsparser import DocsParser
            self.parser = DocsParser(self.client, self.KumoObj)

        elif self.choice.drive in gsuite.SERVICES:
            from sheetsparser import SheetsParser
            self.parser = SheetsParser(self.client, self.KumoObj)
        else:
            raise NotImplementedError('{} service not implemented'.format(self.choice.drive))

        return self.choice

    def prompt_rev_range(self):
        """
        Prompts user for revision range.  Bounds checking added for each particular service as needed
        :return: Tuple consisting of (start, end) revision numbers. 
        """
        start, end = 0, 0

        if self.choice.drive not in gsuite.SERVICES:
            print('{} is not a supported service at this time')
            self.logger.debug('Unsupported service: {}'.format(self.choice.drive))
            raise SystemExit
        elif self.choice.drive == 'presentation':
            self.logger.debug('Non document drive - setting revision to 1, max_revs')
            start, end = 1, self.choice.max_revs
            print('Partial revisions for {} are not supported. Setting start=1 and end=max'.format(self.choice.drive))
        else:
            print('Please choose revision range\n')
            start = self._start_rev_range(start=start)
            end = self._end_rev_range(start=start, end=end)

        self.choice_start, self.choice_end = start, end
        return start, end

    def _start_rev_range(self, start):
        """ Prompts for start revision with bounds checking"""
        while start < 1 or start > self.choice.max_revs:
            try:
                start = int(raw_input("Start from revision(max {}): ".format(self.choice.max_revs)))
                if start < 1 or start > self.choice.max_revs:
                    raise ValueError
            except ValueError:
                print("invalid start revision choice\n")
        return start

    def _end_rev_range(self, start, end):
        """ Prompts for end revision with bounds checking"""
        while end < start or end > self.choice.max_revs:
            try:
                end = int(raw_input("End at revision(max {}): ".format(self.choice.max_revs)))
                if end == 0 or end > self.choice.max_revs:
                    raise ValueError
            except ValueError:
                print("invalid end revision choice\n")
        return end

    def get_log(self, start, end, **kwargs):
        """
        Gets log from the google api client using self.choice data along with starting and ending revision 
        :param start: Starting revision
        :param end: Ending revision
        :param kwargs: Unused here, as the necessary information is in self.choice 
        :return: Native revision log
        """

        return self.parser.get_log(start=start, end=end, choice=self.choice)

    def flatten_log(self, log):
        """Splits into snapshot and changelog, parses each, and returns flat log"""
        # TODO take out flat_log by reference
        flat_log = []
        try:
            self.parser.parse_snapshot(log['chunkedSnapshot'], flat_log)
            self.parser.parse_log(log['changelog'], flat_log)
        except KeyError:
            self.logger.exception('Missing chunkedSnapshot or changelog keys in log')
            raise

        return flat_log

    def recover_objects(self, log, flat_log, choice):
        return self.parser.recover_objects(log, flat_log, choice)

    def make_base_path(self):
        revision_range = '{start}-{end}'.format(start=self.choice_start, end=self.choice_end)
        if os.path.isabs(self.base_dir):
            base_path = os.path.realpath(self.base_dir)
        else:
            base_path = os.path.realpath(os.path.join(KIOutils.kumo_working_directory(), self.base_dir,
                                                      self.choice.drive, self.choice.title, revision_range))
        return base_path

    def write_objects(self, *objects):
        """ Writes all objects recovered from log """

        base_path = self.make_base_path()
        KIOutils.ensure_path(base_path)
        for obj in objects:
            self.write_object(obj, base_path)


if __name__ == '__main__':
    print('hi')
