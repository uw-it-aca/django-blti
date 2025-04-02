# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from pylti1p3.contrib.django.request import DjangoRequest


class BLTIRequest(DjangoRequest):
    def __init__(self, request, post_only=False, default_params=None):
        super().__init__(request, post_only, default_params)

    def set_request_cookie(self, key, value):
        self._request.COOKIES[key] = value
