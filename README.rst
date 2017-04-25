--------
Kumodocs
--------

A tool for GSuite acquisition and analysis that can be easily extended through module creation to other services.
Kumodocs retrieves cloud-native artifacts, internal data structures that maintain SaaS/web app state information.
These artifacts have no presence on the local machine. 
In GSuite collaboration services, these cloud natives have the form of append-only logs that track each minor change to a document.
Kumodocs processes these logs to retrieve comments, suggestions, plain-text, drawings, and deleted images for any given revision.

Kumodocs currently supports Google Docs and Google Slides.
Google drive contents are retrieved and the user is prompted to choose a file. 
The revision log for that file is obtained and processed for the artifacts mentioned above. 

Configuration
~~~~~~~~~~~~~ 
Google API requires OAuth2 authentication to access drive services.
An app must be created and registered at Google project Credentials_ page, where the client_id and 
client_secret can be found.  These must be added to config/gdrive_config.json

Installation
~~~~~~~~~~~~
Requirements include:

- OAuth2 client ID and client secret from https://console.developers.google.com/apis/credentials
- Python 2.7.x
- google-api-python-client==1.6.2 
- click==6.7
- virtualenv (optional) 


1. Get a client ID and client secret
---------------------------------
First, Kumodocs needs an OAuth 2.0 client ID and client secret to make requests to Google's sign-in endpoints.

To find your project's client ID and client secret, do the following:

1. Open the Credentials_ page.

.. _Credentials: https://console.developers.google.com/apis/credentials

2. If you haven't done so already, create your project's OAuth 2.0 credentials by clicking Create credentials > OAuth client ID, and providing the information needed to create the credentials.  Select "Other" as the type. 

3. Look for the Client ID and client secret in the OAuth 2.0 client IDs section. For details, click the client ID.

4. Add the client ID and client secret to config/gdrive_config.json 

2. Python Program
----------------------

The recommended method of installation is to create a virtual environment using the virtualenv python package ::

$ cd kumodocs
$ virtualenv kumodocs

Activate the virtual environment by using source activate (linux) or running activate.bat (windows) ::

$ source kumodocs/bin/activate (linux)  ||  kumodocs\Scripts\activate.bat (windows) 

A new virtual environment is created, where installation will not cause changes to the path or modify existing python packages.  Installation can be completed by::

$ pip install --editable . 

This will install the required packages and create a kumodocs executable usable from anywhere. 

Alternatively, required packages can be installed with pip via::

$ pip install -r requirements.txt 

Executing ``python kumodocs.py`` will start the service.

Usage
~~~~~

If using virtualenv and kumodocs is on path: 

.. code::

   kumodocs || kumodocs -h, --help for options 

If packages are locally installed:

.. code::

   python kumodocs.py -h, --help




Known Limitations and Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Sheets and Forms modules are not implemented yet.
- Slides do not support starting revisions higher than 1


Contact Information
~~~~~~~~~~~~~~~~~~~

Author:  Shane McCulley <smcculle@uno.edu>

 - Project: https://github.com/kumofx/kumodocs
 - Issues: https://github.com/kumofx/kumodocs/issues
