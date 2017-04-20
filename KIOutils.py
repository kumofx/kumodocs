import ConfigParser
import Tkinter as Tk
import errno
import logging
import ntpath
import os
import re
import shutil
import tempfile
import tkFileDialog
from contextlib import contextmanager

REL_CONFIG_PATH = ['config', 'config.cfg']


def dir_path(fname):
    """ Returns full directory path of the current file """
    return os.path.dirname(os.path.realpath(fname)).strip()


def get_log_path():
    """ Returns the full directory path of the log file """
    filename = 'log.log'
    return os.path.join(dir_path(__file__), 'config', filename)


def init_log():
    """ Starts basic log configuration """
    # TODO add to a configuration file
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s: %(name)s - %(levelname)s - %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=get_log_path(),
                        filemode='w')


init_log()
log = logging.getLogger(__name__)


def strip_invalid_characters(filename):
    """
    Very conservative stripping of extraneous characters in filename.  Characters and underscore allowed.
    :param filename: File name obtained from cloud service
    :return: 
    """
    new_filename_partial = re.sub('[^\w\-_. ]', '_', filename)
    new_filename = re.sub('__+', '_', new_filename_partial)
    log.debug('Stripped invalid characters from filename: {} -> {}'.format(filename.encode('utf-8'), new_filename))
    return new_filename


def split_title(title):
    """
    Separates filename and drive type into a tuple. 
    :param title: File title with drive extension
    :return: A tuple of title, drive 
    """
    ext_index = title.rfind('.')
    drive = title[ext_index + 1:]
    title = strip_path_extension(title[:ext_index])
    if drive in ['drawing', 'form', 'spreadsheet']:
        drive += 's'
        print('drive is now', drive)
    return title, drive


def strip_path_extension(path):
    """ Returns filename by stripping extension from basename"""
    basename = ntpath.basename(path)
    return os.path.splitext(basename)[0]


def choose_file_dialog(**options):
    """ Creates an open file dialog to choose a file, and returns a handle to that file """
    root = Tk.Tk()
    root.geometry('0x0+400+400')
    root.wait_visibility()
    root.wm_attributes('-alpha', 0.0)
    root.lift()
    root.focus_force()
    chosen_files = tkFileDialog.askopenfile(**options)
    root.destroy()
    return chosen_files


def ensure_path(path):
    """ Attempts to make a directory and raises exception if there is an issue"""
    try:
        os.makedirs(path)
    except OSError as exception:
        # if the directory exists, ignore error
        if exception.errno != errno.EEXIST:
            log.exception('I/O error creating directory at: {}'.format(path))
            raise


def remove_directory(path):
    """ Deletes all files and removes directory at path"""
    try:
        shutil.rmtree(path)
    except IOError as e:
        # if the directory does not exist, ignore error
        if e.errno != errno.ENOENT:
            log.exception('I/O error removing temp files at: {}'.format(path))
            raise


def get_abs_config_path():
    """
    Creates absolute paths for config files and reads them. 
    :return: Tuple (token_path, client_secrets_path) required for oauth2. 
    """
    config = ConfigParser.ConfigParser()
    file_dir = dir_path(__file__)
    config_fp = os.path.realpath(os.path.join(file_dir, *REL_CONFIG_PATH))
    config.read(config_fp)
    tokens = config.get('gsuite', 'tokenfile').split('/')
    client_secrets = config.get('gsuite', 'configurationfile').split('/')
    token_path = os.path.join(file_dir, *tokens)
    client_secrets_path = os.path.join(file_dir, *client_secrets)
    return token_path, client_secrets_path


@contextmanager
def temp_directory():
    """ Creates and removes temporary directory using WITH statement """
    path = tempfile.mkdtemp()
    try:
        yield path
    finally:
        remove_directory(path)
