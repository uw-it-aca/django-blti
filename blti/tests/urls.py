# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf.urls import include
from django.urls import re_path
from blti.views import BLTIRawView


urlpatterns = [
    re_path(r'^$', BLTIRawView.as_view(), name='lti-launch'),
    re_path(r'^blti/', include('blti.urls')),
]
