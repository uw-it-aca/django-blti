[![Build Status](https://api.travis-ci.org/uw-it-aca/django-blti.svg?branch=master)](https://travis-ci.org/uw-it-aca/django-blti)
[![Coverage Status](https://coveralls.io/repos/uw-it-aca/django-blti/badge.png?branch=master)](https://coveralls.io/r/uw-it-aca/django-blti?branch=master)

Django BLTI Provider
=================

A Django application on which to build IMS BLTI Tool Providers

Installation
------------

**Project directory**

Install django-blti in your project.

    $ cd [project]
    $ pip install django-blti==1.2

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
