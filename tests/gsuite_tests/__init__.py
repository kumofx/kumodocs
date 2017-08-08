import hashlib
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

SAMPLES = {'document': TestCase(DocsHandler, FileChoice(file_id='1AD0Shz2av1uXAr3Uea36QZCUNOHhh6cuv2FD4qxtsdM',
                                                        title='docstest', drive='document', max_revs=75)),
           'presentation': TestCase(SlidesHandler, FileChoice(file_id='1MLX72bIOxQf9zm3HYtN8NXN8BEkkPQ5oXiwfddtVDe8',
                                                              title='slidestest', drive='presentation', max_revs=150)),
           'spreadsheet': TestCase(SheetsHandler, FileChoice(file_id='1-90_i4MLgjGQzLVRUrYjmoymJB0JftsYvWG6DS0wqpY',
                                                             title='sheetstest', drive='spreadsheet', max_revs=8)),
           'drawing': TestCase(SlidesHandler, FileChoice(file_id='1BRGVuBA6-dJihXOUyEtGQ34sWM4NlKjEwDNEQWnQGyc',
                                                         title='drawingstest', drive='drawing', max_revs=74))}


class TestDriver(GSuiteDriver):
    def __init__(self):
        super(TestDriver, self).__init__()
        self.log, self.flat_log = None, None

    def clear(self):
        """ Clear attributes for the next test """
        self.log, self.flat_log, self.choice, self._parser = None, None, None, None


test_driver = TestDriver()


def get_driver(drive_type):
    """ Given a drive type, returns driver with parser and choice listed in SAMPLES """
    sample = SAMPLES[drive_type]
    test_driver.clear()
    test_driver.parser = sample.parser(test_driver.client)
    test_driver.choice = sample.choice
    return test_driver


def check_img(fn, content, hashes):
    """ Checks hash of content against hashes """
    assert hashlib.md5(content).hexdigest() in hashes, '{} does not match samples'.format(fn)


def check_doc(fn, content, sample):
    """ Loads text doc named fn from sample dir and verifies match with content """
    fp = os.path.abspath(os.path.join(KIOutils.dir_path(__file__), 'samples', sample, fn))
    with open(fp, 'rb') as f:
        sample_content = f.read()
    assert sample_content == content, \
        '{}(len={}) != {}(len={})'.format('sample', len(sample_content), fn, len(content))


def hash_sample_images(sample):
    """ Given sample, returns set of all image hashes found in dir """
    sample_images = read_sample_images(sample)
    return {hashlib.md5(img).hexdigest() for img in sample_images}


def is_image(filename):
    """ Sample files are either text or image - checks if filename is pdf or txt """
    return not (filename.endswith('.pdf') or filename.endswith('.txt'))


def read_sample_images(sample):
    """ Reads all images from given sample"""
    base_dir = os.path.abspath(os.path.join(KIOutils.dir_path(__file__), 'samples', sample))
    files = (f for f in os.listdir(base_dir) if is_image(f))
    objects = []
    for fn in files:
        fp = os.path.join(base_dir, fn)
        with open(fp, 'rb') as f:
            objects.append(f.read())
    return objects


def check_recover_objects(driver):
    sample = driver.choice.title
    log = driver.get_log(start=1, end=driver.choice.max_revs)
    flat_log = driver.flatten_log(log)
    objects = [(o.filename, o.content) for o in driver.recover_objects(log=log, flat_log=flat_log,
                                                                       choice=driver.choice)]
    hashes = hash_sample_images(sample)
    for fn, content in objects:
        if fn.endswith('.txt'):
            yield check_doc, fn, content, sample
        else:
            yield check_img, fn, content, hashes
