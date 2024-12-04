# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf.urls import include
from django.urls import re_path

urlpatterns = [
    re_path(r'^blti/', include('blti.urls')),
]
