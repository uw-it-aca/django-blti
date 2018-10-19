from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from oauthlib.oauth1.rfc5849.request_validator import RequestValidator
from oauthlib.oauth1.rfc5849.utils import UNICODE_ASCII_CHARACTER_SET
from blti.models import BLTIKeyStore
from blti import BLTIException
import time
import re


class BLTIRequestValidator(RequestValidator):
    def __init__(self):
        self._client_secret = None

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
        client_secret = self.get_client_secret(client_key, request)
        if client_secret == self.dummy_client:
            return False
        return True

    def get_client_secret(self, client_key, request):
        if self._client_secret is None:
            try:
                self._client_secret = BLTIKeyStore.objects.get(
                    consumer_key=client_key).shared_secret
            except BLTIKeyStore.DoesNotExist:
                try:
                    self._client_secret = getattr(
                        settings, 'LTI_CONSUMERS', {})[client_key]
                except KeyError:
                    self._client_secret = self.dummy_client
        return self._client_secret

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

    RE_ROLE_NS = re.compile(r'^urn:lti:(?:inst|sys)?role:ims/lis/([A-Za-z]+)$')

    def authorize(self, blti, role='member'):
        if blti is None:
            raise BLTIException('Missing LTI parameters')

        lti_consumer = blti.data.get(
            'tool_consumer_info_product_family_code', '').lower()

        if lti_consumer == 'canvas':
            if (not role or role == 'public'):
                pass
            elif (role in self.CANVAS_ROLES):  # member/admin
                self._has_role(blti, self.CANVAS_ROLES[role])
            else:  # specific role?
                self._has_role(blti, [role])
        else:
            raise BLTIException('authorize() not implemented for "%s"!' % (
                lti_consumer))

    def _has_role(self, blti, valid_roles):
        roles = blti.data.get('roles', '').split(',')
        for role in roles:
            if role in valid_roles:
                return

            m = self.RE_ROLE_NS.match(role)
            if m and m.group(1) in valid_roles:
                return

        raise BLTIException('You are not authorized to view this content')
