#!/usr/bin/env python

import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-blti',
    version='0.5',
    packages=['blti'],
    include_package_data=True,
    install_requires = [
        'setuptools',
        'django',
        'oauth2',
        'PyCrypto'
    ],
    license='Apache License, Version 2.0',  # example license
    description='A Django Application on which to build IMS BLTI Tool Providers',
    long_description=README,
    url='https://github.com/uw-it-aca/django-blti',
    author = "UW-IT ACA",
    author_email = "mikes@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
)
