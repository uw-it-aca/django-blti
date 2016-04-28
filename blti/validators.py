from django.conf import settings
from blti.models import BLTIKeyStore
from blti import BLTIException
from oauth import oauth
import urllib
import time
import re


class BLTIDataStore(oauth.OAuthDataStore):
    """
    Implments model- and settings-based OAuthDataStores
    """
    def lookup_consumer(self, key):
        try:
            model = BLTIKeyStore.objects.get(consumer_key=key)
            return BLTIConsumer(key, model.shared_secret)

        except BLTIKeyStore.DoesNotExist:
            try:
                consumers = getattr(settings, 'LTI_CONSUMERS', {})
                return BLTIConsumer(key, consumers[key])
            except KeyError:
                return None

    def lookup_nonce(self, oauth_consumer, oauth_token, nonce):
        return nonce if oauth_consumer.CheckNonce(nonce) else None


class BLTIConsumer(oauth.OAuthConsumer):
    """
    OAuthConsumer superclass that adds nonce caching
    """
    def __init__(self, key, secret):
        oauth.OAuthConsumer.__init__(self, key, secret)
        self.nonces = []

    def CheckNonce(self, nonce):
        """
        Returns True if the nonce has been checked in the last hour
        """
        now = time.time()
        old = now - 3600.0
        trim = 0
        for n, t in self.nonces:
            if t < old:
                trim = trim + 1
            else:
                break
        if trim:
            self.nonces = self.nonces[trim:]

        for n, t in self.nonces:
            if n == nonce:
                return True

        self.nonces.append((nonce, now))


class BLTIOauth(object):
    def validate(self, request, params={}):
        oauth_server = oauth.OAuthServer(data_store=BLTIDataStore())
        oauth_server.add_signature_method(
            oauth.OAuthSignatureMethod_HMAC_SHA1())

        oauth_request = oauth.OAuthRequest.from_request(
            request.method,
            request.build_absolute_uri(),
            headers=request.META,
            parameters=params
        )

        if oauth_request:
            try:
                consumer = oauth_server._get_consumer(oauth_request)
                oauth_server._check_signature(oauth_request, consumer, None)
                return oauth_request.get_nonoauth_parameters()
            except oauth.OAuthError as err:
                raise BLTIException(err)

        raise BLTIException('Invalid OAuth Request')


class BLTIRoles(object):
    ADMIN = 'admin'
    MEMBER = 'member'
    ALL = None

    # https://www.imsglobal.org/specs/ltiv1p1/implementation-guide#toc-19
    LIS_ADMIN = [
        'AccountAdmin', 'SysAdmin', 'SysSupport', 'Faculty', 'Staff',
        'Creator', 'Administrator',
        'Administrator/Administrator', 'Administrator/Developer',
        'Administrator/ExternalDeveloper', 'Administrator/ExternalSupport',
        'Administrator/ExternalSystemAdministrator', 'Administrator/Support',
        'Administrator/SystemAdministrator',
        'Manager', 'Manager/AreaManager', 'Manager/CourseCoordinator',
        'Manager/ExternalObserver', 'Manager/Observer'
    ]

    LIS_INSTRUCTOR = [
        'Instructor',
        'Instructor/ExternalInstructor', 'Instructor/GuestInstructor',
        'Instructor/Lecturer', 'Instructor/PrimaryInstructor',
        'TeachingAssistant',
        'TeachingAssistant/Grader', 'TeachingAssistant/TeachingAssistant',
        'TeachingAssistant/TeachingAssistantGroup',
        'TeachingAssistant/TeachingAssistantOffering',
        'TeachingAssistant/TeachingAssistantSection',
        'TeachingAssistant/TeachingAssistantSectionAssociation',
        'TeachingAssistant/TeachingAssistantTemplate'
    ]

    LIS_LEARNER = [
        'Alumni', 'Guest', 'Learner', 'Member', 'ProspectiveStudent',
        'Student', 'Learner', 'Learner/ExternalLearner',
        'Learner/GuestLearner', 'Learner/Instructor', 'Learner/Learner',
        'Learner/NonCreditLearner', 'Member', 'Member/Member'
    ]

    def _has_role(self, roles, lis_roles):
        for role in roles:
            if role in lis_roles:
                return True

            m = re.match(r'^urn:lti:(inst|sys)?role:ims/lis/([A-Za-z]+)$',
                         role)
            if m and m.group(2) in lis_roles:
                return True

        return False

    def has_admin_role(self, roles):
        return self._has_role(roles, self.LIS_ADMIN)

    def has_instructor_role(self, roles):
        return self._has_role(roles, self.LIS_INSTRUCTOR)

    def has_learner_role(self, roles):
        return self._has_role(roles, self.LIS_LEARNER)

    def validate(self, blti, visibility):
        if visibility:
            roles = ','.join([blti.get('roles', ''),
                              blti.get('ext_roles', '')]).split(',')

            # ADMIN includes instructors, MEMBER includes
            if not (self.has_admin_role(roles) or
                    self.has_instructor_role(roles) or
                    (visibility == self.MEMBER and
                    self.has_learner_role(roles))):
                raise BLTIException(
                    'You do not have privilege to view this content.')
