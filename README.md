ACA BLTI Provider
=================

A Django Application on which to build IMS BLTI Tool Providers

Installation
------------

**Project directory**

Install Support Tools in your project.

    $ cd [project]
    $ pip install -e git+https://github.com/uw-it-aca/django-blti/#egg=django_blti

Project settings.py
------------------

**INSTALLED_APPS**

    # global blti app
    'blti',
    
**MIDDLEWARE_CLASSES**

    'django.middleware.common.CommonMiddleware',
    'blti.middleware.CSRFHeaderMiddleware',
    'blti.middleware.SessionHeaderMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

**BLTI App settings**

     # BLTI consumer key:secret pairs
     LTI_CONSUMERS = {
         '<unique_cousumer_key>': '<32_or_more_bytes_of_entropy>'
     }

     # BLTI session object encryption values
     BLTI_AES_KEY = b'<AES128_KEY>'
     BLTI_AES_IV = b'<AES128_INIT_VECTOR>'

Project urls.py
---------------
    # support urls
    url(r'^blti/', include('blti.urls')),
