# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


"""
Cross Site Request Forgery and Session HTTP Header Middleware.

This module provides middleware that implements protection
against request forgeries from other sites.
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import authenticate, login
from blti import BLTI
from blti.exceptions import BLTIException


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


class LTISessionAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            lti_launch_parameters = BLTI().get_session(request)
            lti_user = lti_launch_parameters.get(
                "https://purl.imsglobal.org/spec/lti/claim/custom", {}).get(
                    "canvas_user_login_id")
            if lti_user:
                user = authenticate(request, remote_user=lti_user)
                login(request, user)
        except BLTIException:
            pass

        return self.get_response(request)


class SameSiteMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if 'sessionid' in response.cookies:
            response.cookies['sessionid']['samesite'] = 'None'
        if 'csrftoken' in response.cookies:
            response.cookies['csrftoken']['samesite'] = 'None'
        return response
