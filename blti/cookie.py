# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import http.cookies as Cookie
from pylti1p3.contrib.django.cookie import DjangoCookieService
import django  # type: ignore
import logging


logger = logging.getLogger(__name__)


if "partitioned" not in Cookie.Morsel._flags:
    Cookie.Morsel._flags.add("partitioned")
if "partitioned" not in Cookie.Morsel._reserved:
    Cookie.Morsel._reserved.setdefault("partitioned", "Partitioned")


class BLTICookieService(DjangoCookieService):
    def __init__(self, request):
        return super().__init__(request)

    def get_cookie(self, name):
        logger.info(f"get_cookie: {name}")
        return super().get_cookie(name)

    def set_cookie(self, name, value, exp=3600):
        logger.info(f"set_cookie: {name}: {value}")
        return super().set_cookie(name, value, exp)

    def update_response(self, response):
        super().update_response(response)

        for key, cookie_data in self._cookie_data_to_set.items():
            if self._request.is_secure():
                response.cookies[key]["Partitioned"] = True
                logger.info(f"BLTICookieService: {key}: set Partitioned")
            else:
                logger.info(f"BLTICookieService: {key}: insecure request")
