# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from pylti1p3.request import Request


class BLTIRequest(Request):
    def __init__(self, request, post_only=False, default_params=None):
        super().__init__(request, post_only, default_params)

    def get_origin(self):
        return self._request.META.get('HTTP_ORIGIN')
