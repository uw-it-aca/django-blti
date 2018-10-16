"""
Cross Site Request Forgery and Session HTTP Header Middleware.

This module provides a middleware that implements protection
against request forgeries from other sites.
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CSRFHeaderMiddleware(MiddlewareMixin):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        csrf_token = request.META.get('HTTP_X_CSRFTOKEN', None)
        if csrf_token is not None:
            csrf_token_name = settings.CSRF_COOKIE_NAME
            request.COOKIES[csrf_token_name] = csrf_token

        return None


class SessionHeaderMiddleware(MiddlewareMixin):
    def process_request(self, request):
        session_id = request.META.get('HTTP_X_SESSIONID', None)
        if session_id is not None:
            session_key = settings.SESSION_COOKIE_NAME
            request.COOKIES[session_key] = session_id
