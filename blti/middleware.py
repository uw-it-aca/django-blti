# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


"""
Cross Site Request Forgery and Session HTTP Header Middleware.

This module provides middleware that implements protection
against request forgeries from other sites.
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CSRFHeaderMiddleware(MiddlewareMixin):
    def process_request(self, request):
        csrf_token = request.META.get('HTTP_X_CSRFTOKEN', None)
        if csrf_token is not None:
            csrf_token_name = settings.CSRF_COOKIE_NAME
            request.COOKIES[csrf_token_name] = csrf_token


class SessionHeaderMiddleware(MiddlewareMixin):
    def process_request(self, request):
        session_id = request.META.get('HTTP_X_SESSIONID', None)
        if session_id is not None:
            session_key = settings.SESSION_COOKIE_NAME
            request.COOKIES[session_key] = session_id


class SameSiteMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if 'sessionid' in response.cookies:
            response.cookies['sessionid']['samesite'] = 'None'
        if 'csrftoken' in response.cookies:
            response.cookies['csrftoken']['samesite'] = 'None'
        return response
