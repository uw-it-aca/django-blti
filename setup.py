import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/django-blti>`_.
"""

# The VERSION file is created by travis-ci, based on the tag name
version_path = 'blti/VERSION'
VERSION = open(os.path.join(os.path.dirname(__file__), version_path)).read()
VERSION = VERSION.replace("\n", "")

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-blti',
    version=VERSION,
    packages=['blti'],
    include_package_data=True,
    install_requires=[
        'Django>2.1,<3.0',
        'oauth2',
        'PyCrypto',
    ],
    license='Apache License, Version 2.0',
    description='A Django Application on which to build IMS BLTI Tool Providers',
    long_description=README,
    url='https://github.com/uw-it-aca/django-blti',
    author="UW-IT AXDD",
    author_email="aca-it@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
)
