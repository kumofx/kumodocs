"""Common methods for initializing GSuite API client and listing GSuite files. """

import argparse
import json
import logging
import os
import sys
from collections import defaultdict

# noinspection PyPackageRequirements
import googleapiclient.discovery
# noinspection PyPackageRequirements
import googleapiclient.errors
import httplib2
import oauth2client.client as oa_client
import oauth2client.file as oa_file
import oauth2client.tools as oa_tools

import KIOutils
import gsuite

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class Client(object):
    """ Wraps a googleapiclient service object with functionality needed by multiple GSuite modules """

    def __init__(self, service="drive", scope='https://www.googleapis.com/auth/drive'):
        self.service = self.start(service, scope)

    def start(self, service_name, scope='https://www.googleapis.com/auth/drive'):
        """
        Reads config file and initializes the GSuite API client with proper authentication
        :param service_name: Name of service to start, one of gsuite.SERVICES
        :param scope: API scope to authorize.  Defaults to read/manage files in Google Drive.  
        :return: Google API client for making requests. 
        """

        log.info('Creating the client service')
        tokens, client_secrets = KIOutils.get_abs_config_path()
        flow = oa_client.flow_from_clientsecrets(client_secrets,
                                                 scope=scope,
                                                 message=oa_tools.message_if_missing(client_secrets))
        storage = oa_file.Storage(tokens)
        credentials = storage.get()

        # run_flow requires a wrapped oa_tools.argparse object to handle command line arguments
        flags = argparse.ArgumentParser(parents=[oa_tools.argparser])
        if credentials is None:  # or credentials.invalid:
            if self.has_client_secrets(client_secrets):
                credentials = oa_tools.run_flow(flow, storage, flags)
            else:
                raise NotImplementedError(oa_tools.message_if_missing(client_secrets))

        # noinspection PyBroadException
        try:
            http = credentials.authorize(httplib2.Http())
            client = googleapiclient.discovery.build(serviceName=service_name, version="v2", http=http,
                                                     cache_discovery=False)
        except Exception as e:
            log.error('Failed to create service', exc_info=True)
            raise sys.exit(1)
        else:
            log.info('Created and authorized the client service')
            return client

    def has_client_secrets(self, client_secrets):
        """ Returns true if client_id and client_secrets set in file client_secrets"""
        with open(client_secrets) as json_data:
            secrets = json.load(json_data)['installed']

        client_id = secrets['client_id']
        client_secret = secrets['client_secret']
        return not client_id.startswith('<GET') and not client_secret.startswith('<GET')

    def request(self, url, **kwargs):
        """
        Sends an http request using underlying authenticated httplib2 object from the google api client. 
        :param url: URL to request 
        :param kwargs: Optional request args such as header, body, etc. 
        :return: Tuple consisting of response code and content 
        """

        try:
            response, content = self.service._http.request(url, **kwargs)
            if response['status'] != '200':
                log.critical('gapiclient.request has non-200 response status, but not httperror exception')
                log.debug('response = {}'.format(response))
                log.debug('content = {}'.format(content))
                raise googleapiclient.errors.HttpError
        except googleapiclient.errors.HttpError:
            log.exception('Could not obtain log. Check file_id, max revisions, and permission for file')
        else:
            return response, content

    def choose_file(self):
        """
        Presents user with drive contents and prompts a choice.  
        :return: FileChoice named tuple with id, title, drive, and max revisions
        """
        files = self.list_all_files()

        with KIOutils.temp_directory() as temp_dir:
            self.create_temp_files(temp_dir, files)
            options = {'title': 'Choose a G Suite file', 'initialdir': temp_dir}
            choice = KIOutils.choose_file_dialog(**options)

            try:
                file_id = choice.read()
            except AttributeError as e:
                log.error('No file chosen. Exiting.')
                sys.exit(2)
            except IOError as e:
                log.error('Error reading file. Exiting')
                sys.exit(3)
            else:
                choice.close()
                title, drive = KIOutils.split_title(choice.name)
                log.info('Chose file {} from service {}'.format(title, drive))

        revisions = self.service.revisions().list(fileId=file_id, fields='items(id)').execute()
        max_revs = revisions['items'][-1]['id']

        choice = gsuite.FileChoice(str(file_id), title, drive, int(max_revs))
        log.debug('Choice is {}'.format(choice))
        return choice

    def list_all_files(self):
        """
        Retrieve a list of File resources from the google API client. 
        :return: List of File resources 
        """

        result = defaultdict(list)
        page_token = None
        for drive_type in gsuite.SERVICES:
            while True:
                param = {'q': gsuite.MIME_TYPE.format(drive_type),
                         'fields': 'items(title, id)'}
                if page_token:
                    param['pageToken'] = page_token

                try:
                    files = self.service.files().list(**param).execute()
                except googleapiclient.errors.HttpError, e:
                    log.error('Failed to retrieve list of files', exc_info=True)
                    break
                else:
                    result[drive_type].extend(files['items'])
                    page_token = files.get('nextPageToken')
                    if not page_token:
                        break
        return result

    @staticmethod
    def create_temp_files(temp_dir, files):
        """
        Creates a directory of temporary files with file_id for virtualization of drive contents
        :param temp_dir: A temp directory that will be deleted 
        :param files: A file list resource returned from the API client list method
        :return: None
        """

        for drive_type, drive_files in files.items():
            folder_path = os.path.join(temp_dir, drive_type + '/')
            os.mkdir(folder_path)
            for file_ in drive_files:
                # replace reserved characters in title to assure valid filename
                filename = KIOutils.strip_invalid_characters(file_['title'])
                filename = '{}.{}'.format(os.path.join(temp_dir, folder_path, filename), drive_type)
                with open(filename, 'w') as f:
                    f.write(file_['id'])

    @staticmethod
    def get_download_ext(html_response):
        """ 
        Returns extension for downloaded resource as formatted for GSuite API html response
        :param html_response:  GSuite API html response 
        :return: Extension of downloaded resource (png, pdf, doc, etc)
        """
        cdisp = html_response['content-disposition']
        start_index = cdisp.index('.')
        end_index = cdisp.index('"', start_index)
        extension = cdisp[start_index:end_index]
        return extension

    @staticmethod
    def create_log_url(start, end, choice):
        params = gsuite.REV_PARAMS.format(start=start, end=end)
        log_url = gsuite.API_BASE.format(drive=choice.drive, file_id=choice.file_id, params=params)
        return log_url
