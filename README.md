# Django BLTI Provider

[![Build Status](https://github.com/uw-it-aca/django-blti/workflows/tests/badge.svg?branch=main)](https://github.com/uw-it-aca/django-blti/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/django-blti/badge.svg?branch=main)](https://coveralls.io/github/uw-it-aca/django-blti?branch=main)
[![PyPi Version](https://img.shields.io/pypi/v/django-blti.svg)](https://pypi.python.org/pypi/django-blti)
![Python versions](https://img.shields.io/pypi/pyversions/django-blti.svg)


A Django application on which to build IMS BLTI Tool Providers

Installation
------------

**Project directory**

Install django-blti in your project.

    $ cd [project]
    $ pip install django-blti

Project settings.py
------------------

**INSTALLED_APPS**

    'blti',

**MIDDLEWARE_CLASSES**

    'django.middleware.common.CommonMiddleware',
    'blti.middleware.CSRFHeaderMiddleware',
    'blti.middleware.SessionHeaderMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

**Additional settings**

     # BLTI consumer key:secret pairs
     LTI_CONSUMERS = {
         '<unique_consumer_key>': '<32_or_more_bytes_of_entropy>'
     }

     # BLTI session object encryption values
     BLTI_AES_KEY = b'<AES128_KEY>'
     BLTI_AES_IV = b'<AES128_INIT_VECTOR>'

Project urls.py
---------------
    url(r'^blti/', include('blti.urls')),
