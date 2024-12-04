[![Build Status](https://github.com/uw-it-aca/django-blti/workflows/tests/badge.svg?branch=main)](https://github.com/uw-it-aca/django-blti/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/django-blti/badge.svg?branch=main)](https://coveralls.io/github/uw-it-aca/django-blti?branch=main)
[![PyPi Version](https://img.shields.io/pypi/v/django-blti.svg)](https://pypi.python.org/pypi/django-blti)
![Python versions](https://img.shields.io/badge/python-3.10-blue.svg)

# Documentation

django-blti is a Django web framework application intended so serve
as a base for [IMS LTI 1.3](https://www.imsglobal.org/spec/lti/v1p3)
Tool projects. It implements common class-based views providing launch
authentication, payload normalization, and role based authorization.
It also includes optional endpoints for tool development based on
mock payloads.  We understand and regret that the ``b`` in the package
name is a little misleading, but it is what it is.

## Installation
```
    $ pip install django-blti
```
## Django Configuration
It should be sufficient to add the app and supporting settings to ``project/settings.py``:
```
    INSTALLED_APPS += ['blti']

    # add session authentication based on lauch authentication
    MIDDLEWARE_CLASSES += [
        'blti.middleware.SessionHeaderMiddleware',
        'blti.middleware.CSRFHeaderMiddleware',
        'blti.middleware.SameSiteMiddleware'
        'blti.middleware.LTISessionAuthenticationMiddleware',]

    # relax samesite requirements, limit casual snooping
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # only necessary when running behind ingress proxy
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_SCHEME', 'https')

```
and expose the necessary authentication endpoints in ``project/urls.py``:
```
    url(r'^blti/', include('blti.urls')),
```
## Class Based View
A tool is implemented by subclassing ``blti.views.BLTILaunchView``.

After successful launch authentication, the instance variable
``self.blti`` will hold the normalized payload data provided by
the class's ``self.launch_data_model`` method.  The default method
provides a normalized data model for the Canvas LTI Platform.

Access control is applied based on the view's class variable:
```
    authorized_role = 'member'
```
In addition to LTI-defined roles the following rollup roles are
also supported:
* public - no access restrictions
* member - viewable by staff, instructors, students, and observers
* admin - viewable by staff, instructors, and content developers
## LTI Tool Configuration
Deployed tool configuration is defined in the JSON file named
``tool.json`` in the location defined by the environment variable:
```
    LTI_CONFIG_DIRECTORY = /etc/lti-config
```
The configuration file content is documented in the
[pylti1p3 README](https://github.com/dmitry-viskov/pylti1.3?tab=readme-ov-file#configuration).

In addition, a management command is available to simplify key
pair generation during configuration.
```
    # python manage.py generate_credentials private.key public.key jwt.json
```
## Tool Development
This app also provides an optional development environment activated by
defining the environment variable:
```
    LTI_DEVELOP_APP=my_app
```
and launch url named:
```
    urlpatterns = [
        re_path(r'^$', MyToolLaunchView.as_view(), name="lti-launch"),
    ]
```
And finally, to initiate the launch sequence, point your browser at ``/blti/dev``

A mocked JWT payload for Canvas is provided, but can be overridden by
creating the file ``resources/lti1p3/file/jwt.json`` in your tool's
app directory. django-blti will walk the list of ``INSTALLED_APPS``,
and use the first file by that name discovered.
### Project Examples
Visit [uw-id-aca/info-hub-lti](https://github.com/uw-it-aca/info-hub-lti) or
[uw-id-aca/library-guides-lti](https://github.com/uw-it-aca/library-guides-lti) or
to see LTI Tool  examples based on launch views and mocked local development
environment.
## Legacy Support
LTI 1.1 launch authentication, authorization, and payload normalization is
also supported for the time being, but is no longer documented here.
