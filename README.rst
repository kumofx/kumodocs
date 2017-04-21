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
An app must be created and registered at https://code.google.com/apis/console/, where the client_id and 
client_secret can be found.  These must be added to config/gdrive_config.json

Installation
~~~~~~~~~~~~
Requirements include:

- Python 2.7.x
- google-api-python-client==1.6.2 
- click==6.7
- virtualenv (optional) 

The recommended method of installation is to create a virtual environment using the virtualenv python package ::

$ cd kumodocs
$ virtualenv kumodocs
$ source kumodocs/bin/activate || kumodocs\Scripts\activate.bat (windows) 

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