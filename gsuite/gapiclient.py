"""Common methods for initializing GSuite API client and listing GSuite files. """
import json
import logging
import os
import sys
from collections import defaultdict

# noinspection PyPackageRequirements
import googleapiclient.discovery
# noinspection PyPackageRequirements
import googleapiclient.errors
# noinspection PyPackageRequirements
import httplib2
import oauth2client.client as oa_client
import oauth2client.file as oa_file
import oauth2client.tools as oa_tools

import KIOutils
import gsuite

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Client(object):
    """ Wraps a googleapiclient service object with functionality needed by multiple GSuite modules """

    HttpError = googleapiclient.errors.HttpError

    def __init__(self, service="drive", scope='https://www.googleapis.com/auth/drive'):
        self.service = self.start(service, scope)

    def start(self, service_name, scope='https://www.googleapis.com/auth/drive'):
        """
        Reads config file and initializes the GSuite API client with proper authentication
        :param service_name: Name of service to start, one of gsuite.SERVICES
        :param scope: API scope to authorize.  Defaults to read/manage files in Google Drive.  
        :return: Google API client for making requests. 
        """

        logger.info('Creating the client service')
        tokens, client_secrets = KIOutils.get_abs_config_path()
        flow = oa_client.flow_from_clientsecrets(client_secrets,
                                                 scope=scope,
                                                 message=oa_tools.message_if_missing(client_secrets))
        storage = oa_file.Storage(tokens)
        credentials = storage.get()

        if credentials is None:  # or credentials.invalid:
            if self.has_client_secrets(client_secrets):
                credentials = oa_tools.run_flow(flow, storage, flags=None)
            else:
                raise NotImplementedError(oa_tools.message_if_missing(client_secrets))

        # noinspection PyBroadException
        try:
            http = credentials.authorize(httplib2.Http())
            client = googleapiclient.discovery.build(serviceName=service_name, version="v2", http=http,
                                                     cache_discovery=False)
            client.http = http  # directly expose http without using 'protected' _http
        except Exception:
            logger.error('Failed to create service', exc_info=True)
            raise sys.exit(1)
        else:
            logger.info('Created and authorized the client service')
            return client

    @staticmethod
    def has_client_secrets(client_secrets):
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
            response, content = self.service.http.request(url, **kwargs)
            if response['status'] != '200':
                logger.critical('status {} returned for url {}'.format(response['status'], url))
                logger.debug('response = {}'.format(response))
                logger.debug('content = {}'.format(content))
                raise self.HttpError(resp=response, content=content, uri=url)
        except self.HttpError:
            logger.debug('HttpError in gapiclient', exc_info=True)
            raise
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
            except AttributeError:
                logger.error('No file chosen. Exiting.')
                sys.exit(2)
            except IOError:
                logger.error('Error reading file. Exiting')
                sys.exit(3)
            else:
                choice.close()
                title, drive = KIOutils.split_title(choice.name)
                logger.info('Chose file "{}" from service "{}"'.format(title, drive))

        revisions = self.service.revisions().list(fileId=file_id, fields='items(id)').execute()
        max_revs = revisions['items'][-1]['id']

        choice = gsuite.FileChoice(str(file_id), title, drive, int(max_revs))
        logger.debug('Choice is {}'.format(choice))
        return choice

    def list_all_files(self):
        """
        Retrieve a list of File resources from the google API client. 
        :return: List of File resources 
        """

        logger.info('Retrieving list of drive files')
        result = defaultdict(list)
        page_token = None
        email = self.email_address()
        for drive_type in gsuite.LOG_DRIVE:
            while True:
                param = {'q': gsuite.Q_PARAM.format(email=email, drive_type=drive_type),
                         'fields': 'items(title, id), nextPageToken'}
                if page_token:
                    param['pageToken'] = page_token

                try:
                    files = self.service.files().list(**param).execute()
                except googleapiclient.errors.HttpError:
                    logger.error('Failed to retrieve list of files', exc_info=True)
                    break
                else:
                    result[drive_type].extend(files['items'])
                    page_token = files.get('nextPageToken')
                    if not page_token:
                        break
        return result

    def email_address(self):
        """ Returns email address for the currently authenticated user """
        about_me = self.service.about().get(fields='user(emailAddress)').execute()
        return about_me['user']['emailAddress']

    def fetch_comments(self, file_id, fields):
        contents = self.service.comments().list(fileId=file_id, includeDeleted=True, fields=fields).execute()
        comments = contents['items']
        return comments

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
    def create_log_url(start, end, choice):
        drive = gsuite.LOG_DRIVE[choice.drive]
        params = gsuite.REV_PARAMS.format(start=start, end=end)
        log_url = gsuite.API_BASE.format(drive=drive, file_id=choice.file_id, params=params)
        return log_url
