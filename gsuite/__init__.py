import logging
from collections import namedtuple

# package-level constants defined below
API_BASE = 'https://docs.google.com/{drive}/d/{file_id}/{params}'
REV_PARAMS = 'revisions/load?start={start}&end={end}'
RENDER_PARAMS = 'renderdata?id={file_id}'
MIME_TYPE = "mimeType = 'application/vnd.google-apps.{}'"
SERVICES = ['document', 'presentation', 'spreadsheet', 'drawing']
LOG_DRIVE = {'document': 'document', 'spreadsheet': 'spreadsheets', 'drawing': 'drawings',
             'presentation': 'presentation', 'form': 'forms'}
DRAW_PARAMS = 'image?w={w}&h={h}'
CHUNKED_ORDER = ['si', 'ei', 'st']
LOG_START_CHR = ")]}'\n"

# package-level named tuples
FileChoice = namedtuple('FileChoice', 'file_id, title, drive, max_revs')
Drawing = namedtuple('Drawing', 'd_id width height')


# custom exceptions
class InvalidLogFormat(Exception):
    """ Unable to parse log due to invalid format or LOG_START_CHR """
    pass


# package level functions
def log_msg(cls, msg, error_level):
    """
    Package-level method logs msg with given error_lvl to a logger created with cls name.
    :param cls: Instance of class object calling the logger
    :param msg: Message to log
    :param error_level Error level to log message at
    :return: None
    """
    logger = logging.getLogger(cls.__class__.__name__)
    log_func = getattr(logger, error_level)
    log_func(msg)
