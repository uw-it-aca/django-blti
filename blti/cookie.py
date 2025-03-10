# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import http.cookies as Cookie
from pylti1p3.contrib.django import DjangoCookieService
import logging


logger = logging.getLogger(__name__)


if "partitioned" not in Cookie.Morsel._flags:
    Cookie.Morsel._flags.add("partitioned")
if "partitioned" not in Cookie.Morsel._reserved:
    Cookie.Morsel._reserved.setdefault("partitioned", "Partitioned")


class LTICookieService(DjangoCookieService):
    def get_cookie(self, name):
        logger.info(f"get_cookie: {name} ==> {self._request.get_cookie(self._get_key(name))}")
        return self._request.get_cookie(self._get_key(name))

    def set_cookie(self, name, value, exp=3600):
        logger.info(f"set_cookie: {name} ({self._get_key(name)}) ==> {value}")
        self._cookie_data_to_set[self._get_key(name)] = {
            "value": value,
            "exp": exp,
        }

    def update_response(self, response):
        logger.info(f"update_response: {self._cookie_data_to_set}")
        for key, cookie_data in self._cookie_data_to_set.items():
            kwargs = {
                "value": cookie_data["value"],
                "max_age": cookie_data["exp"],
                "secure": self._request.is_secure(),
                "httponly": True,
                "path": "/",
            }

            if self._request.is_secure():
                # samesite argument was added in Django 2.1, but samesite could be set as None only from Django 3.1
                # https://github.com/django/django/pull/11894
                django_support_samesite_none = django.VERSION[0] > 3 or (
                    django.VERSION[0] == 3 and django.VERSION[1] >= 1
                )

                # SameSite=None and Secure=True are required to work inside iframes
                if django_support_samesite_none:
                    kwargs["samesite"] = "None"
                    response.set_cookie(key, **kwargs)
                else:
                    response.set_cookie(key, **kwargs)
                    response.cookies[key]["samesite"] = "None"

                response.cookies[key]["Partitioned"] = True
            else:
                response.set_cookie(key, **kwargs)


