import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/django-blti>`_.
"""

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
        'Django>=3.2,<5',
        'oauthlib',
        'cryptography',
        'mock',
        'PyLTI1p3==2.0.0',
    ],
    license='Apache License, Version 2.0',
    description='A Django Application on which to build IMS BLTI Tool Providers',
    long_description=README,
    url='https://github.com/uw-it-aca/django-blti',
    author="UW-IT T&LS",
    author_email="aca-it@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
