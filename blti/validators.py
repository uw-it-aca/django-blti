from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from blti.models import BLTIKeyStore
from blti import BLTIException
import oauth2 as oauth
import re


class BLTIOauth(object):
    def __init__(self):
        if not hasattr(settings, 'LTI_CONSUMERS'):
            raise ImproperlyConfigured('Missing setting LTI_CONSUMERS')

    def validate(self, request, params={}):
        oauth_server = oauth.Server()
        oauth_server.add_signature_method(
            oauth.SignatureMethod_HMAC_SHA1())

        oauth_request = oauth.Request.from_request(
            request.method,
            request.build_absolute_uri(),
            headers=request.META,
            parameters=params
        )

        if oauth_request:
            try:
                key = oauth_request.get_parameter('oauth_consumer_key')
                consumer = self.get_consumer(key)
                oauth_server._check_signature(oauth_request, consumer, None)
                return oauth_request.get_nonoauth_parameters()
            except oauth.Error as err:
                raise BLTIException(str(err))

        raise BLTIException('Invalid OAuth Request')

    def get_consumer(self, key):
        try:
            model = BLTIKeyStore.objects.get(consumer_key=key)
            return oauth.Consumer(key, str(model.shared_secret))

        except BLTIKeyStore.DoesNotExist:
            try:
                consumers = getattr(settings, 'LTI_CONSUMERS', {})
                return oauth.Consumer(key, consumers[key])
            except KeyError:
                raise BLTIException('No Matching Consumer')


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
