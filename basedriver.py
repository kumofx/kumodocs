import os
from abc import abstractmethod, ABCMeta, abstractproperty


# noinspection PyClassHasNoInit
from collections import namedtuple


class BaseDriver(object):
    __metaclass__ = ABCMeta

    class KumoObj(namedtuple('KumoObj', 'filename content')):
        """ A Kumo object retrieved from revision log sharing common properties:
        param str filename: Type of object with extension
        param str content:  String content suitable for writing to disk 
        """
        __slots__ = ()

    @abstractproperty
    def logger(self):
        """
        Defines a logger property that must be provided in the derived class 
        :return: logger property
        :rtype: Instance of logging.Logger
        """
        pass

    @logger.setter
    def logger(self, value):
        """ Defines a basic setter for logger property """
        pass

    @abstractproperty
    def base_dir(self):
        """
        Defines base directory property for recovered objects, with relative paths considering /kumodocs as the 
        working directory. 
        :return: base_directory as absolute or relative path
        :rtype: str
        """
        pass

    @base_dir.setter
    def base_dir(self, value):
        """ Defines a basic setter for base_dir property """
        pass

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
        pass

    @abstractmethod
    def flatten_log(self, log):
        """
        Takes a native revision log and converts to the common log format.  
        :param log: Native revision log from some service
        :return: Flattened log in the common log format.  
        """
        pass

    @abstractmethod
    def recover_objects(self, log, flat_log, choice):
        """ Recovers plain-text from the flat (common) log, as well as any associated 
        objects (images, suggestions, comments, etc ).  
        
        :param log:  Native log retrieved from get_log
        :param flat_log:  Log that has been flattened using flatten_log
        :param choice:  contains necessary file metadata to process
        :return: None; outputs all recovered objects to the location specified by self.write_object
        """
        pass

    @abstractmethod
    def choose_file(self):
        """
        Lists drive options and prompts user for a file choice.  
        :return: Returns necessary information to retrieve the log of this file, such as any file_id, title, 
        and revisions available.  
        :rtype: A namedtuple containing all necessary information (to be sent to get_log as **kwargs) 
        """
        pass

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
