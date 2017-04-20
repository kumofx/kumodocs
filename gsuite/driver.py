import json
import logging
import os
from collections import namedtuple

import KIOutils
import basedriver
import gapiclient


class InvalidLogFormat(Exception):
    pass


class GSuiteDriver(basedriver.BaseDriver):
    """ 
    Functionality to retrieve and flattens Google Docs logs, and recover plain-text, suggestions, comments, 
    and images from the log.
    """

    SuggestionContent = namedtuple('content', 'added, deleted')
    LOG_START_CHR = ")]}'\n"

    def __init__(self, base_dir='../downloaded', delimiter='|'):
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
            self.parser = DocsParser(self.client, self.choice)
        else:
            raise NotImplementedError('{} service not implemented'.format(self.choice.drive))

        return self.choice

    def prompt_rev_range(self):
        """
        Prompts user for revision range.  Bounds checking added for each particular service as needed
        :return: Tuple consisting of (start, end) revision numbers. 
        """
        start, end = 0, 0

        if self.choice.drive not in ['document', 'presentation']:
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
            end = self._end_rev_range(end=end)

        self.choice_start, self.choice_end = start, end
        return start, end

    def _start_rev_range(self, start):
        """ Prompts for start revision with bounds checking"""
        while start < 1 or start >= self.choice.max_revs:
            try:
                start = int(raw_input("Start from revision(max {}): ".format(self.choice.max_revs)))
                if start < 1 or start >= self.choice.max_revs:
                    raise ValueError
            except ValueError:
                print("invalid start revision choice\n")
        return start

    def _end_rev_range(self, end):
        """ Prompts for end revision with bounds checking"""
        while end == 0 or end > self.choice.max_revs:
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

        log_url = self.client.create_log_url(start=start, end=end, choice=self.choice)
        response, log = self.client.request(url=log_url)
        if log.startswith(GSuiteDriver.LOG_START_CHR):
            trimmed_log = log[len(GSuiteDriver.LOG_START_CHR):]
            return json.loads(trimmed_log)
        else:
            raise InvalidLogFormat('Unknown starting log punctuation. Check GSuiteDriver.LOG_START_CHR and compare to '
                                   'log')

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

    def recover_objects(self, log, flat_log):
        image_ids, drawing_ids, suggestions = self.parser.get_doc_objects(flat_log=flat_log)
        plain_text = self.parser.get_plain_text(flat_log=flat_log)

        comments = self.parser.get_comments()  # service, file_id)
        images = self.parser.get_images(image_ids=image_ids,
                                        get_download_ext=self.client.get_download_ext)  # , service, file_id,
        # drive)
        drawings = self.parser.get_drawings(drawing_ids=drawing_ids, drive='drawings',
                                            get_download_ext=self.client.get_download_ext)
        self.write_doc(docname=self.choice.title, plain_text=plain_text, comments=comments, images=images,
                       drawings=drawings, start=self.choice_start, end=self.choice_end, suggestions=suggestions,
                       log=log, flat_log=flat_log)

    # refactor for list(**args)
    def write_doc(self, docname, plain_text, comments, images, drawings, start, end, suggestions, log, flat_log):
        """ Writes all document objects retrieved from the log """
        base_dir = os.path.realpath(os.path.join(
            KIOutils.dir_path(__file__), '..', 'downloaded', 'document', docname, '{}-{}'.format(str(start), str(end))))
        KIOutils.ensure_path(base_dir)
        writing_msg = 'Writing {} to disk'

        self.logger.info(writing_msg.format('drawings'))
        for i, drawing in enumerate(drawings):
            filename = os.path.join(base_dir, 'drawing' + str(i) + drawing[1])
            self.logger.debug('Writing drawing {} with name {}'.format(i, filename))
            with open(filename, 'wb') as f:
                f.write(drawing[0])

        self.logger.info(writing_msg.format('images'))
        for i, img in enumerate(images):
            filename = os.path.join(base_dir, 'img' + str(i) + img[1])
            self.logger.debug('Writing img {} with name {}'.format(i, filename))
            with open(filename, 'wb') as f:
                f.write(img[0])

        filename = os.path.join(base_dir, 'plain.txt')
        with open(filename, 'w') as f:
            self.logger.info(writing_msg.format('plain text'))
            f.write(plain_text.encode('utf-8'))

        filename = os.path.join(base_dir, 'comments.txt')
        with open(filename, 'w') as f:
            self.logger.info(writing_msg.format('comments'))
            f.write('\n'.join(str(line) for line in comments))

        filename = os.path.join(base_dir, 'suggestions.txt')
        with open(filename, 'w') as f:
            self.logger.info(writing_msg.format('suggestions'))
            f.write(json.dumps(suggestions, ensure_ascii=False))

        filename = os.path.join(base_dir, 'revision-log.txt')
        with open(filename, 'w') as f:
            self.logger.info(writing_msg.format('revision log'))
            f.write('chunkedSnapshot')
            for line in log['chunkedSnapshot']:
                f.write(str(line) + '\n')
            f.write('changelog')
            for line in log['changelog']:
                f.write(str(line) + '\n')

        filename = os.path.join(base_dir, 'flat-log.txt')
        with open(filename, 'w') as f:
            self.logger.info(writing_msg.format('flat log'))
            for line in flat_log:
                f.write(line + '\n')

        print '\nFinished with output in directory', base_dir


if __name__ == '__main__':
    print('hi')
