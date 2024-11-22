# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from oauthlib.oauth1.rfc5849.request_validator import RequestValidator
from oauthlib.oauth1.rfc5849.utils import UNICODE_ASCII_CHARACTER_SET
from blti.exceptions import BLTIException
import time
import re


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
    # https://www.imsglobal.org/specs/ltiv1p1/implementation-guide#toc-30
    CANVAS_ROLES = {
        'member': ['Administrator', 'Instructor', 'TeachingAssistant',
                   'ContentDeveloper', 'Learner', 'Observer'],
        'admin': ['Administrator', 'Instructor', 'TeachingAssistant',
                  'ContentDeveloper'],
    }

    RE_ROLE_NS = re.compile(
        r'^urn:lti:(?:inst|sys)?role:ims/lis/([A-Za-z]+)$')
    RE_ROLE_1P3 = re.compile(
        r'^http://purl.imsglobal.org/vocab/lis/v2/.*#([A-Za-z]+)$')

    def authorize(self, launch_data, role='member', consumer='canvas'):
        if launch_data is None:
            raise BLTIException('Missing LTI parameters')

        lti_consumer = self._consumer(launch_data)

        if lti_consumer.lower() == consumer.lower():
            if (not role or role == 'public'):
                pass
            elif (role in self.CANVAS_ROLES):  # member/admin
                self._has_role(launch_data, self.CANVAS_ROLES[role])
            else:  # specific role?
                self._has_role(launch_data, [role])
        else:
            raise BLTIException('authorize() not implemented for "%s"!' % (
                lti_consumer))

    def _consumer(self, launch_data):
        PLATFORM_CLAIM = ('https://purl.imsglobal.org/spec/lti/'
                          'claim/tool_platform')
        try:
            return launch_data['tool_consumer_info_product_family_code']
        except KeyError:
            return launch_data.get(
                PLATFORM_CLAIM, {}).get('product_family_code', '')

    def _has_role(self, launch_data, valid_roles):
        try:
            # 1.1 roles parameter
            roles = launch_data['roles'].split(',')
            for role in roles:
                if role in valid_roles:
                    return

                m = self.RE_ROLE_NS.match(role)
                if m and m.group(1) in valid_roles:
                    return
        except KeyError:
            # 1.3 roles parameter
            roles = launch_data.get(
                "https://purl.imsglobal.org/spec/lti/claim/roles", [])
            for role in roles:
                m = self.RE_ROLE_1P3.match(role)
                if m and m.group(1) in valid_roles:
                    return

        raise BLTIException('You are not authorized to view this content')
