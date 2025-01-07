# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.urls import re_path
from blti.views import login, get_jwks, BLTIRawView


urlpatterns = [
    re_path(r'^login/?$', login, name='login'),
    re_path(r'^jwks/?$', get_jwks, name='jwks'),
    re_path(r'^$', BLTIRawView.as_view(), name='lti-launch-data'),
]

if getattr(settings, 'LTI_DEVELOP_APP', False):
    from blti.views.develop import BLTIDevPrepare, BLTIDevLaunch

    urlpatterns += [
        re_path(r'^dev/?$', BLTIDevPrepare.as_view(), name='dev-prepare'),
        re_path(r'^dev/launch/$', BLTIDevLaunch.as_view(), name='dev-launch'),
    ]
