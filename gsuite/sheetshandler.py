import logging

from baseclass import Handler
# noinspection PyUnresolvedReferences
from gsuite.docshandler import CommentsParser

logger = logging.getLogger(__name__)


class SheetsHandler(Handler):
    @property
    def parsers(self):
        return self._parsers

    @property
    def logger(self):
        return logger

    def __init__(self, client, delimiter=None, parsers=None):
        super(SheetsHandler, self).__init__(client, delimiter)
        self._parsers = [self.init_parser(p) for p in parsers or self.collect_parsers(__name__)]
