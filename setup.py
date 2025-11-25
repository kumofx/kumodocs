from setuptools import setup

setup(
    name='Kumodocs',
    version='0.6',
    packages=['', 'gsuite'],
    url='https://github.com/kumofx/kumodocs',
    license='Apache License 2.0',
    author='Shane McCulley',
    author_email='smcculle@uno.edu',
    description='A tool for GSuite acquisition and analysis that can be easily extended through module creation '
                'to other services. ',
    data_files=[('config', ['config/cfg', 'config/gdrive_config.json'])],
    python_requires='>=3.8',
    install_requires=[
        'click>=8.0.0',
        'google-api-python-client>=2.0.0',
        'google-auth-httplib2>=0.1.0',
        'google-auth-oauthlib>=0.5.0',
        'oauth2client>=4.1.3',
        'pytest>=7.0.0',
        'requests>=2.31.0',
        'selenium>=4.0.0',
    ],
    entry_points='''
        [console_scripts]
        kumodocs=kumodocs:cli
    ''',
)
