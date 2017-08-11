import hashlib
import json
import os
from collections import namedtuple

import KIOutils
from gsuite import FileChoice
from gsuite.docshandler import DocsHandler
from gsuite.driver import GSuiteDriver
from gsuite.sheetshandler import SheetsHandler
from gsuite.slideshandler import SlidesHandler

# sys.path.append(os.path.abspath('.'))

TestCase = namedtuple('TestCase', 'parser choice')

CASES = {'document': TestCase(DocsHandler, FileChoice(file_id='1AD0Shz2av1uXAr3Uea36QZCUNOHhh6cuv2FD4qxtsdM',
                                                      title='docstest', drive='document', max_revs=75)),
         'presentation': TestCase(SlidesHandler, FileChoice(file_id='1MLX72bIOxQf9zm3HYtN8NXN8BEkkPQ5oXiwfddtVDe8',
                                                            title='slidestest', drive='presentation', max_revs=150)),
         'spreadsheet': TestCase(SheetsHandler, FileChoice(file_id='1-90_i4MLgjGQzLVRUrYjmoymJB0JftsYvWG6DS0wqpY',
                                                           title='sheetstest', drive='spreadsheet', max_revs=8)),
         'drawing': TestCase(SlidesHandler, FileChoice(file_id='1BRGVuBA6-dJihXOUyEtGQ34sWM4NlKjEwDNEQWnQGyc',
                                                       title='drawingstest', drive='drawing', max_revs=74))}


class TestDriver(GSuiteDriver):
    @property
    def count(self):
        """ Returns number of objects that should be returned from recover_objects"""
        return len(os.listdir(sample_base_dir(self.choice.title)))

    def __init__(self):
        super(TestDriver, self).__init__()
        self.log, self.flat_log, self.images = None, None, None

    def clear(self):
        """ Clear attributes for the next test """
        self.log, self.flat_log, self.choice, self.parser, self.images = [None] * 5

    def load_case(self, drive):
        """ Loads a TestCase that corresponds to a folder in gsuite_tests/samples """
        self.clear()
        test_case = CASES[drive]
        self.parser = test_case.parser(test_driver.client)
        self.choice = test_case.choice
        self.log = read_log(self.choice.title)
        self.flat_log = read_flat_log(self.choice.title)
        self.images = read_sample_images(self.choice.title)
        return self

    def check_recover_objects(self):
        """ Compares the given handler's recover_objects function against files located in the sample dir"""
        sample = self.choice.title
        objects = {(o.filename, o.content) for o in self.recover_objects(log=self.log, flat_log=self.flat_log,
                                                                         choice=self.choice)}
        assert len(objects) == self.count
        hashes = hash_sample_images(self.images)
        for fn, content in objects:
            if fn.endswith('.txt'):
                yield check_doc, fn, content, sample
            else:
                yield check_img, fn, content, hashes

    def hash_sample_images(self):
        """ Given sample, returns set of all image hashes found in dir """
        return {hashlib.md5(img).hexdigest() for img in self.images}


test_driver = TestDriver()


def check_img(fn, content, hashes):
    """ Checks hash of content against hashes """
    assert hashlib.md5(content).hexdigest() in hashes, '{} does not match samples'.format(fn)


def check_doc(fn, content, sample_title):
    """ Loads text doc named fn from sample dir and verifies match with content """
    fp = os.path.abspath(os.path.join(KIOutils.dir_path(__file__), 'samples', sample_title, fn))
    with open(fp, 'rb') as f:
        sample_content = f.read()
    if fn == 'revision-log.txt':
        content, sample_content = json.loads(content), json.loads(sample_content)
    assert sample_content == content, \
        '{}(len={}) != {}(len={})'.format('sample', len(sample_content), fn, len(content))


def hash_sample_images(images):
    """ Given sample, returns set of all image hashes found in dir """
    return {hashlib.md5(img).hexdigest() for img in images}


def is_image(filename):
    """ Sample files are either text or image - checks if filename is pdf or txt """
    return not (filename.endswith('.pdf') or filename.endswith('.txt'))


def sample_base_dir(sample_title):
    """ Returns the absolute path of the given TestCase sample """
    return os.path.abspath(os.path.join(KIOutils.dir_path(__file__), 'samples', sample_title))


def read_sample_images(sample_title):
    """ Reads all images from given sample"""
    base_dir = sample_base_dir(sample_title)
    files = (f for f in os.listdir(base_dir) if is_image(f))
    objects = []
    for fn in files:
        fp = os.path.join(base_dir, fn)
        with open(fp, 'rb') as f:
            objects.append(f.read())
    return objects


def read_flat_log(sample_title):
    """ Returns the flat log from sample location """
    return read_sample_file(sample_title, 'flat-log.txt').rstrip().split('\n')


def read_log(sample_title):
    """ Returns the log as dict from sample location """
    return json.loads(read_sample_file(sample_title, 'revision-log.txt'))


def read_sample_file(sample_title, filename):
    """ Generic read function for a file in sample directory """
    filepath = os.path.join(sample_base_dir(sample_title), filename)
    with open(filepath, 'rb') as f:
        file_ = f.read()
    return file_
