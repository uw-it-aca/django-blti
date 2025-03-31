# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from pylti1p3.contrib.django.cookie import DjangoCookieService


class BLTICookieService(DjangoCookieService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_request_cookie(self, name, value):
        self._request.set_request_cookie(self._get_key(name), value)
