# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from oauthlib.oauth1.rfc5849.request_validator import RequestValidator
from oauthlib.oauth1.rfc5849.utils import UNICODE_ASCII_CHARACTER_SET
from blti.exceptions import BLTIException
import time
import logging


logger = logging.getLogger(__name__)


class BLTIRequestValidator(RequestValidator):
    @property
    def allowed_signature_methods(self):
        return ['HMAC-SHA1']

    @property
    def dummy_client(self):
        return 'dummy'

    @property
    def client_key_length(self):
        return 12, 30

    @property
    def nonce_length(self):
        return 20, 50

    @property
    def enforce_ssl(self):
        return getattr(
            settings, 'LTI_ENFORCE_SSL', True)

    @property
    def safe_characters(self):
        return set(UNICODE_ASCII_CHARACTER_SET) | set('-_')

    def validate_client_key(self, client_key, request):
        return self.get_client_secret(
            client_key, request) != self.dummy_client

    def get_client_secret(self, client_key, request):
        try:
            return getattr(
                settings, 'LTI_CONSUMERS', {})[client_key]
        except KeyError:
            return self.dummy_client

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
                                     request, request_token=None,
                                     access_token=None):
        now = int(time.time())
        return (now - 60) <= int(timestamp) <= (now + 60)


class Roles(object):
    def __init__(self, launch_data):
        self.blti = launch_data

    def authorize(self, role='member'):
        if not hasattr(self, 'blti') or self.blti is None:
            raise ImproperlyConfigured(
                'Roles class requires a blti model')

        role = role.lower() if role else None
        if not role or role == 'public' or (
                role == 'member' and
                self.blti.is_member) or (
                    role == 'admin' and
                    self.blti.is_administrator) or (
                        role in ['administrator', 'sysadmin'] and
                        self.blti.is_staff) or (
                            role in ['instructor', 'teacher']
                            and self.blti.is_instructor) or (
                                role in ['teachingassistant', 'ta'] and
                                self.blti.is_teaching_assistant) or (
                                    role in ['student', 'learner'] and
                                    self.blti.is_student) or (
                                        role in [
                                            'contentdeveloper', 'designer'] and
                                        self.blti.is_designer):
            return

        raise BLTIException('You are not authorized to view this content')
