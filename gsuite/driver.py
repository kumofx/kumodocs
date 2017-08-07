import json
import logging
import os
from collections import namedtuple

import KIOutils
import gapiclient
import gsuite
from baseclass import Driver
from gsuite.docshandler import DocsHandler
from gsuite.formshandler import FormsHandler
from gsuite.sheetshandler import SheetsHandler
from gsuite.slideshandler import SlidesHandler


class GSuiteDriver(Driver):
    """ 
    Functionality to retrieve and flattens Google Docs logs, and recover plain-text, suggestions, comments, 
    and images from the log.
    """

    SERVICES = {'document': DocsHandler, 'presentation': SlidesHandler, 'drawing': SheetsHandler,
                'spreadsheet': SheetsHandler,
                'form': FormsHandler}

    SuggestionContent = namedtuple('content', 'added, deleted')

    def __init__(self, base_dir='downloaded', delimiter='|', parser=None):
        self.client = gapiclient.Client(service='drive', scope=['https://www.googleapis.com/auth/drive',
                                                                'https://www.googleapis.com/auth/forms'])
        self._logger = logging.getLogger(__name__)
        self._base_dir = base_dir
        self.delimiter = delimiter
        self.choice = None
        self._parser = parser
        self.choice_start = None
        self.choice_end = None

    def init_parser(self, choice=None):
        """ Initializes the correct parser for the given choice"""
        choice = choice or self.choice

        try:
            service_parser = GSuiteDriver.SERVICES[choice.drive]
        except KeyError:
            raise NotImplementedError('{} service not implemented'.format(choice.drive))
        else:
            parser = service_parser(self.client)

        return parser

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
        Presents the user with a virtualized interface of their GSuite contents to choose a file,
        and initializes the appropriate parser for the given drive type.
        :return: A namedtuple containing file_id, title, drive, and max_revs
        """
        self.choice = self.client.choose_file()

        return self.choice

    def prompt_rev_range(self):
        """
        Prompts user for revision range.  Bounds checking added for each particular service as needed
        :return: Tuple consisting of (start, end) revision numbers. 
        """
        start, end = 0, 0

        if self.choice.drive not in GSuiteDriver.SERVICES:
            self.logger.debug('Unsupported service: {}'.format(self.choice.drive))
            print('\n{} is not a supported service at this time'.format(self.choice.drive))
            raise SystemExit('Unsupported service')
        elif self.choice.drive == 'document':
            print('\nPlease choose revision range\n')
            start = self._start_rev_range(start=start)
            end = self._end_rev_range(start=start, end=end)
        else:
            self.logger.debug('Non document drive - setting starting revision to 1')
            start = 1
            print('\nPartial revisions for {} are not supported. Setting start = 1'.format(self.choice.drive))
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
                print("Invalid start revision choice\n")
        return start

    def _end_rev_range(self, start, end):
        """ Prompts for end revision with bounds checking"""
        while end < start or end > self.choice.max_revs:
            try:
                end = int(raw_input("End at revision(max {}): ".format(self.choice.max_revs)))
                if end == 0 or end > self.choice.max_revs:
                    raise ValueError
            except ValueError:
                print("Invalid end revision choice\n")
        return end

    def log_headers(self):
        """
        Try to get any headers required for log retrieval.
        :return: Headers from parser, none if not implemented
        """
        header_func = getattr(self.parser, 'log_headers', None)
        headers = None
        if header_func:
            try:
                headers = self.parser.log_headers()
            except BaseException as e:
                self.logger.exception(e)
                raise

        return headers

    def get_log(self, start, end, **kwargs):
        """
        Gets log from the google api client using self.choice data along with starting and ending revision 
        :param start: Starting revision
        :param end: Ending revision
        :param kwargs: Optional choice parameter for retrieving other logs
        :return: Native revision log
        """

        self.logger.info('Retrieving revision log')
        choice = kwargs.get('choice', self.choice)
        self.parser = self.init_parser()
        log_url = self.client.create_log_url(start=start, end=end, choice=choice)
        response, log = self.client.request(url=log_url, headers=self.log_headers())
        if log.startswith(gsuite.LOG_START_CHR):
            trimmed_log = log[len(gsuite.LOG_START_CHR):]
        else:
            self.logger.debug('Beginning of log = {}'.format(log[:10]))
            raise gsuite.InvalidLogFormat('Check gsuite.LOG_START_CHR and compare to beginning of log')

        return json.loads(trimmed_log)

    def flatten_log(self, log):
        """ Initializes proper parser which converts revision log into flat_log """

        return self.parser.flatten_log(log)

    def recover_objects(self, log, flat_log, choice):
        """
        Runs available parsers to recover any objects
        :param log: Raw revision log
        :param flat_log: Flattened revision log
        :param choice: gsuite.FileChoice representing choice
        :return:
        """

        return self.parser.recover_objects(log=log, flat_log=flat_log, choice=choice)

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
            KIOutils.ensure_path(os.path.join(base_path, os.path.dirname(obj.filename)))
            self.write_object(obj, base_path)

