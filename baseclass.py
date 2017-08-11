import inspect
import itertools
import json
import os
import sys
from abc import abstractmethod, ABCMeta, abstractproperty
# noinspection PyClassHasNoInit
from collections import namedtuple

import gsuite


def is_parser(item):
    """ Finds all parsers in the current module that are not Parser """
    name, cls = item
    return inspect.isclass(cls) and name.endswith('Parser') and cls is not Parser


class Driver(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def logger(self):
        """
        Defines a logger property that must be provided in the derived class 
        :return: logger property
        :rtype: Instance of logging.Logger
        """

    @logger.setter
    def logger(self, value):
        """ Defines a basic setter for logger property """

    @abstractproperty
    def base_dir(self):  # type: () -> str
        """
        Defines base directory property for recovered objects, with relative paths considering /kumodocs as the 
        working directory. 
        :return: base_directory as absolute or relative path
        """

    @base_dir.setter
    def base_dir(self, value):
        """ Defines a basic setter for base_dir property """

    @abstractmethod
    def get_log(self, start, end, **kwargs):
        """
        Returns the native revision log for this driver's service.  
        :param start: Starting revision
        :param end: Ending revision
        :param kwargs: Any additional information required to retrieve the log (extra credentials, file_id, resources, 
        path, etc)
        :return: unparsed(native) revision log 
        """

    @abstractmethod
    def flatten_log(self, log):
        """
        Takes a native revision log and converts to the common log format.  
        :param log: Native revision log from some service
        :return: Flattened log in the common log format.  
        """

    @abstractmethod
    def recover_objects(self, log, flat_log, choice):
        """ Recovers plain-text from the flat (common) log, as well as any associated 
        objects (images, suggestions, comments, etc ).  
        
        :param log:  Native log retrieved from get_log
        :param flat_log:  Log that has been flattened using flatten_log
        :param choice:  contains necessary file metadata to process
        :return: None; outputs all recovered objects to the location specified by self.write_object
        """

    @abstractmethod
    def choose_file(self):
        """
        Lists drive options and prompts user for a file choice.  
        :return: Returns necessary information to retrieve the log of this file, such as any file_id, title, 
        and revisions available.  
        :rtype: A namedtuple containing all necessary information (to be sent to get_log as **kwargs)
        """

    @abstractmethod
    def prompt_rev_range(self):
        """
        Prompts the user for a start and end revision range.  Possible values depend upon driver implementation and 
        service limitations.  
        :return: A tuple (start, end) 
        :rtype: (int, int) 
        """

    def write_object(self, kumo_obj, base_path):
        """
        Writes object to disk at location specified in directory
        :param kumo_obj: An object to write, containing originating service, file_name, start and end revision,
        as well as content and object type. 
        :param base_path: Directory in which kumo_obj will be written.
        :return: None
        """

        outfile = os.path.realpath(os.path.join(base_path, kumo_obj.filename))
        self.logger.info('Writing {} to disk'.format(kumo_obj.filename))
        self.logger.debug('Writing {} to disk at location {}'.format(kumo_obj.filename, outfile))

        try:
            with open(outfile, 'wb') as f:
                f.write(kumo_obj.content)
        except IOError:
            self.logger.exception('Failed to write {} object'.format(kumo_obj.filename))


class Parser(object):
    """ Specific parsers implement parse() and return a list of KumoObj """
    __metaclass__ = ABCMeta

    def __init__(self, client, delimiter='|'):
        self.KumoObj = Handler.KumoObj
        self.client = client
        self.delimiter = delimiter

    @abstractproperty
    def logger(self):
        """ Local logger object"""

    @abstractmethod
    def parse(self, log, flat_log, choice, **kwargs):
        """
        Main method recovers information from args and returns a list of KumoObj
        :param log: Revision log
        :param flat_log: Flattened revision log
        :param choice: Package-level constant that encapsulates info necessary to parse
        :return: List of KumoObj retrieved from logs
        """


class Handler(object):
    """  Base class for service handlers to inherit.  Any Handler that inherits from this base class should add the
    following to init:

        self._parsers = [self.init_parser(p) for p in parsers or self.collect_parsers(__name__)]

    This will gather any classes defined in the module as xxxxParser as well as any imports
    that match this pattern """

    MESSAGE = """\n\nself._parsers = [self.init_parser(p) for p in parsers or self.collect_parsers(__name__)]

    This will gather any classes defined in the module as xxxxParser as well as any imports
    that match this pattern """

    __metaclass__ = ABCMeta

    DELIMITER = '|'

    class KumoObj(namedtuple('KumoObj', 'filename content')):
        """ A Kumo object retrieved from revision log sharing common properties:
        param str filename: Type of object with extension
        param str content:  String content suitable for writing to disk
        """

        # iter(KumoObj) returns 1 instance of self instead of field members
        @property
        def iter_count(self):
            return self._iter_count

        # noinspection PyAttributeOutsideInit
        @iter_count.setter
        def iter_count(self, value):
            self._iter_count = value

        def __iter__(self):
            self.iter_count = 1
            return self

        def next(self):
            if self.iter_count:
                self.iter_count -= 1
                return self
            else:
                raise StopIteration

    @abstractproperty
    def logger(self):
        """ Local logger """

    @abstractproperty
    def parsers(self):  # type:  () -> list
        """ List of parser instances retrieved during __init__ """

    def __init__(self, client, delimiter=None):
        """ Initializes the handler with client object and optional delimiter, default '|'.  Subclasses should
        implement __init__ with super() and call

            self._parsers = [self.init_parser(p) for p in parsers or self.collect_parsers(__name__)]

        This will gather any classes defined in the module as xxxxParser as well as any imports
        that match this pattern  """

        self.client = client
        self.delimiter = delimiter or self.DELIMITER
        self.parser_opt_args = {}

    # override for service-specific implementation
    def parser_opts(self, log, flat_log, choice):  # type: (dict, str, gsuite.FileChoice) -> dict
        """ Override to provide extra args to parsers """
        return {}

    def parse_log(self, log):
        """
        Override with service-specific requirements
        :return: Must return a list of lines parsed from self.log
        """
        return []

    def parse_snapshot(self, log):
        """ Override with service-specific requirements
        :return: Must return a list of lines parsed from self.log
        """
        return []

    @staticmethod
    def stringify(log):
        """ Returns log in a writable form.  May be overridden for customization"""
        return json.dumps(log, indent=1)

    class FlatParser(Parser):
        """ Converts flat_log to a KumoObj for writing"""

        @property
        def logger(self):
            return None

        def parse(self, log, flat_log, choice, **kwargs):
            if flat_log:
                filename = 'flat-log.txt'
                content = '\n'.join(str(line) for line in flat_log)
                return [self.KumoObj(filename=filename, content=content)]
            else:
                return []

    class LogParser(Parser):
        """ Converts log to a KumoObj for writing"""

        @property
        def logger(self):
            return None

        def parse(self, log, flat_log, choice, **kwargs):
            filename = 'revision-log.txt'
            content = Handler.stringify(log)
            return [self.KumoObj(filename=filename, content=content)]

    # common methods
    def collect_parsers(self, mod_name):
        """ Collects any class ending in `Parser` as well as self.LogParser and self.FlatParser"""
        p = [self.LogParser, self.FlatParser]
        p.extend(cls for name, cls in filter(is_parser, inspect.getmembers(sys.modules[mod_name])))
        return p

    def flatten_log(self, log):
        """
        Splits self.log into snapshot and changelog, parses each, and returns flat_log
        :return: A 1-D log separated by self.delimiter containing action dictionary as last element
        """
        flat_log = []
        try:
            flat_log.extend(self.parse_snapshot(log['chunkedSnapshot']))
            flat_log.extend(self.parse_log(log['changelog']))
        except KeyError:
            self.logger.exception('Missing chunkedSnapshot or changelog keys in log')
            raise

        return flat_log

    def init_parser(self, parser):
        """ Initializes each parser with the required attributes """
        return parser(self.client)

    def recover_objects(self, log, flat_log, choice):
        """ Runs parse() for each parser in self.parser to recover objects from log and flat_log.
        :return: A list of recovered KumoObj
        """
        opt_args = self.parser_opts(log, flat_log, choice)
        objects = list(itertools.chain.from_iterable(p.parse(log, flat_log, choice, **opt_args) for p in self.parsers))

        return objects
