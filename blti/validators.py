from django.conf import settings
from blti.models import BLTIKeyStore
from blti import BLTIException
import oauth2 as oauth
import re


class BLTIOauth(object):
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
                raise BLTIException(err)

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
                return None


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
