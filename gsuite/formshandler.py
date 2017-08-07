import StringIO
import fnmatch
import hashlib
import logging
import os
import platform
import subprocess
import sys
import time
import zipfile

import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

import KIOutils
from baseclass import Handler

logger = logging.getLogger(__name__)


def default_chrome_path():
    return os.path.abspath(os.path.join(KIOutils.kumo_working_directory(), 'chromedriver'))


class ChromeDriver(object):
    START_PAGE = 'file:///{}'.format(os.path.join(KIOutils.kumo_working_directory(), 'gsuite', 'resources',
                                                  'redirect.html'))
    LANDING_PAGE = 'https://myaccount.google.com/?pli=1'
    LATEST_RELEASE = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'
    CHROMEDRIVER_OS_VALS = {
        'Windows32': ('https://chromedriver.storage.googleapis.com/{ver}/chromedriver_win32.zip', None),
        'darwin': ('https://chromedriver.storage.googleapis.com/{ver}/chromedriver_mac64.zip', None),
        'Linux64': ('https://chromedriver.storage.googleapis.com/{ver}/chromedriver_linux64.zip',
                    ['chmod', 'u+x', 'chromedriver']),
        'Linux32': ('https://chromedriver.storage.googleapis.com/{ver}/chromedriver_linux32.zip',
                    ['chmod', 'u+x', 'chromedriver'])}

    def __init__(self, chrome_path=default_chrome_path()):
        self.logger = logging.getLogger('ChromeDriver')
        logger.info('Starting the Chrome service')
        self.downloaded = False
        self.cmd = None
        self.chrome_path = chrome_path

    def __enter__(self):
        self.driver = self.start_driver()
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        if self.downloaded:
            try:
                self.delete_chromedriver()
            except OSError:
                logger.info('Failed to remove chromedrive')
            else:
                self.downloaded = False
                logger.info('Chromedriver removed')

    def delete_chromedriver(self):
        basepath = os.path.abspath(os.path.join(self.chrome_path, '..'))
        filenames = (os.path.join(basepath, f) for f in fnmatch.filter(os.listdir(basepath), 'chromedriver*'))
        for f in filenames:
            os.remove(f)

    @staticmethod
    def get_architecture():
        return '{os}{bits}'.format(os=platform.system(), bits=64 if sys.maxsize > 2 ** 32 else 32)

    def download_chromedriver(self, path=KIOutils.kumo_working_directory(), attempts=3):
        os_url = self.get_url()
        while attempts:
            try:
                logger.debug('URL requested: {}'.format(os_url))
                r = requests.get(os_url, stream=True)
                md5_hash = r.headers['ETag'][1:-1]
                if hashlib.md5(r.content).hexdigest() != md5_hash:
                    raise requests.exceptions.RequestException('Download error, hash invalid')
                else:
                    attempts = 0
            except requests.exceptions.RequestException:
                attempts -= 1
                logger.error('Error obtaining chromedriver. Retrying ({})'.format(attempts))
            else:
                zipf = zipfile.ZipFile(StringIO.StringIO(r.content))
                zipf.extractall(path=path)
                self.downloaded = True
                logger.info('Chromedriver downloaded')
        if not self.downloaded:
            raise SystemExit('Could not download chromedriver.')

        if self.cmd:
            subprocess.Popen(self.cmd)

    def latest_release(self):
        return float(requests.get(self.LATEST_RELEASE).text)

    def get_url(self):
        try:
            os_url, self.cmd = self.CHROMEDRIVER_OS_VALS[self.get_architecture()]
            os_url = os_url.format(ver=self.latest_release())
        except KeyError:
            logger.exception('Cannot find chromedriver for unknown OS type')
            raise SystemExit('Unknown OS type: {}'.format(sys.platform))

        return os_url

    def find_chromedriver(self):
        """ Looks in path, then in Kumo directory for chromedriver """
        try:
            driver = webdriver.Chrome()
        except WebDriverException:
            try:
                driver = webdriver.Chrome(executable_path=self.chrome_path)
            except WebDriverException:
                raise
        return driver

    def start_driver(self):
        try:
            driver = self.find_chromedriver()
        except WebDriverException:
            logger.error('Unable to locate chromedriver')
            time.sleep(0.1)
            download = raw_input('\nNo chrome driver found.  Download? (y/n): ')
            if download.lower().startswith('y'):
                self.download_chromedriver()
                try:
                    driver = webdriver.Chrome(executable_path=self.chrome_path)
                except WebDriverException as e:
                    if 'cannot find' in e.msg:
                        logger.critical('Could not start Chrome browser')
                        raise SystemExit('Forms log cannot be retrieved without Chrome and chromedriver.')
                    else:
                        logger.exception('Cannot start the Chrome browser')
                        raise SystemExit('Forms log cannot be retrieved without Chrome and chromedriver.')

            else:
                raise SystemExit('Forms log cannot be retrieved without Chrome and chromedriver.')

        return driver


class FormsHandler(Handler):
    @property
    def parsers(self):
        return self._parsers

    @property
    def logger(self):
        return logger

    def __init__(self, client, delimiter=None, parsers=None):
        super(FormsHandler, self).__init__(client, delimiter)
        self._parsers = [self.init_parser(p) for p in parsers or self.collect_parsers(__name__)]
        self.required_cookies = ['HSID', 'SSID', 'SID']

    def log_headers(self):
        headers = {'cookie': ''}
        logger.info('NOTE: Forms requires additional authorization.  Opening Chrome to input credentials')
        cookies = self.get_cookies()
        for cookie in cookies:
            if cookie['name'] in self.required_cookies:
                headers['cookie'] += '{}={};'.format(str(cookie['name']), str(cookie['value']))
        return headers

    @staticmethod
    def get_cookies():
        with ChromeDriver() as driver:
            driver.get(ChromeDriver.START_PAGE)
            logger.info('Waiting for authorization... check Chrome page')
            while driver.current_url != ChromeDriver.LANDING_PAGE:
                time.sleep(0.1)
            try:
                logger.info('Authorization successful')
                cookies = driver.get_cookies()
            except WebDriverException:
                raise SystemExit('Could not retrieve credentials from Chrome')
            else:
                return cookies
