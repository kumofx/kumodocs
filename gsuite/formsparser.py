import StringIO
import hashlib
import json
import os
import sys
import time
import zipfile

import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

import KIOutils
from gsuite import log_msg


class ChromeDriver(object):
    LOGIN_PAGE = 'https://accounts.google.com/signin/v2/identifier?flowName=GlifWebSignIn&flowEntry=ServiceLogin'
    LANDING_PAGE = 'https://myaccount.google.com/?pli=1'
    LATEST_RELEASE = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'
    CHROMEDRIVER_OS_URL = {
        'win32': 'https://chromedriver.storage.googleapis.com/{}/chromedriver_win32.zip',
        'darwin': 'https://chromedriver.storage.googleapis.com/{}/chromedriver_mac64.zip',
        'linux2': (
            'https://chromedriver.storage.googleapis.com/{}/chromedriver_linux32.zip',
            ['chmod', 'u+x', 'chromedriver']),
        'linux': (
            'https://chromedriver.storage.googleapis.com/{}/chromedriver_linux32.zip', ['chmod', 'u+x', 'chromedriver'])
    }

    def __init__(self):
        log_msg(self, msg='Starting the Chrome service', error_level='info')
        self.downloaded = False
        self.cmd = None
        self.chrome_path = os.path.abspath(os.path.join(KIOutils.kumo_working_directory(), 'chromedriver'))
        self.driver = self.start_driver()
        if self.cmd:
            import subprocess
            subprocess.Popen(self.cmd)

    def __enter__(self):
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        if self.downloaded:
            try:
                os.remove(self.chrome_path)
                self.downloaded = False
                log_msg(self, msg='Chromedriver removed', error_level='info')
            except WindowsError:
                log_msg(self, msg='Failed to remove chromedr', error_level='info')

    def download_chromedriver(self, path=KIOutils.kumo_working_directory(), attempts=3):
        os_url = self.get_url()
        print "os url is", os_url
        while attempts:
            try:
                log_msg(self, 'URL requested: {}'.format(os_url), 'debug')
                r = requests.get(os_url, stream=True)
                md5_hash = r.headers['ETag'][1:-1]
                if hashlib.md5(r.content).hexdigest() != md5_hash:
                    raise requests.exceptions.RequestException('Download error, hash invalid')
                else:
                    attempts = 0
            except requests.exceptions.RequestException:
                attempts -= 1
                log_msg(self, msg='Error obtaining chromedriver. Retrying ({})'.format(attempts), error_level='error')
            else:
                zipf = zipfile.ZipFile(StringIO.StringIO(r.content))
                zipf.extractall(path=path)
                self.downloaded = True
                log_msg(self, msg='Chromedriver downloaded', error_level='info')
        if not self.downloaded:
            raise SystemExit('Could not download chromedriver.')

    def latest_release(self):
        return float(requests.get(self.LATEST_RELEASE).text)

    def get_url(self):
        try:
            os_url, self.cmd = self.CHROMEDRIVER_OS_URL[sys.platform].format(self.latest_release())
        except KeyError:
            log_msg(self, msg='Cannot find chromedriver for unknown OS type', error_level='exception')
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
            sys.path.append(KIOutils.kumo_working_directory())
            driver = self.find_chromedriver()
        except WebDriverException:
            log_msg(self, msg='Unable to locate chromedriver', error_level='error')
            time.sleep(0.1)
            download = raw_input('\nNo chrome driver found.  Download? (y/n): ')
            if download.lower().startswith('y'):
                self.download_chromedriver()
                driver = webdriver.Chrome(executable_path=self.chrome_path)
            else:
                raise SystemExit('Forms log cannot be retrieved without Chrome and chromedriver.')

        return driver


# TODO refactor all service requests to gapiclient

class FormsParser(object):
    def __init__(self, client, kumo_obj, delimiter='|'):
        self.log = None
        self.flat_log = None
        self.delimiter = delimiter
        self.client = client
        self.service = client.service  # api service
        self.KumoObj = kumo_obj
        self.required_cookies = ['HSID', 'SSID', 'SID']

        # parsers

    def recover_objects(self, log, flat_log, choice):
        """ Recovers plain text, comments, images, drawings, and suggestions from flat_log. 
        :return: A list of recovered objects as KumoObj
        """
        objects = []

        if flat_log:
            objects.extend([self.KumoObj(filename='flat-log.txt', content='\n'.join(str(line) for line in flat_log))])
        objects.extend([self.KumoObj(filename='revision-log.txt', content=json.dumps(log, indent=2))])
        return objects

    def log_headers(self):
        headers = {'cookie': ''}
        log_msg(self, 'NOTE: Forms requires additional authorization.  Opening Chrome to input credentials', 'info')
        cookies = self.get_cookies()
        for cookie in cookies:
            if cookie['name'] in self.required_cookies:
                headers['cookie'] += '{}={};'.format(str(cookie['name']), str(cookie['value']))
        return headers

    def get_cookies(self):
        with ChromeDriver() as driver:
            driver.get(ChromeDriver.LOGIN_PAGE)
            log_msg(self, 'Waiting for authorization... check Chrome page', 'info')
            while driver.current_url != ChromeDriver.LANDING_PAGE:
                time.sleep(0.1)
            try:
                log_msg(self, 'Authorization successful', 'info')
                cookies = driver.get_cookies()
            except WebDriverException:
                raise SystemExit('Could not retrieve credentials from Chrome')
            else:
                return cookies

    def parse_log(self, c_log):
        """ Log flattening not implemented yet"""
        return []

    def parse_snapshot(self, snapshot):
        """ Log flattening not implemented yet"""
        return []
