from setuptools import setup

setup(
    name='Kumodocs',
    version='0.1',
    packages=['', 'gsuite'],
    url='https://github.com/kumofx/kumodocs',
    license='Apache License 2.0',
    author='Shane McCulley',
    author_email='smcculle@uno.edu',
    description='A tool for GSuite acquisition and analysis that can be easily extended through module creation '
                'to other services. ',
    data_files=[('config', ['config/cfg', 'config/gdrive_config.json'])],
    install_requires=['click', 'google-api-python-client'],
    entry_points='''
        [console_scripts]
        kumodocs=kumodocs:cli
    ''',
)
