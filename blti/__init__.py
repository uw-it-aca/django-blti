import json
import urllib
from base64 import b64decode, b64encode
from django.conf import settings
from blti.crypto import aes128cbc
from blti.oauth import validate as oauth_validate
from oauth import OAuthError
import re


class BLTIException(Exception):
    pass


class BLTI(object):
    """
    Basic LTI Validator
    """

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

    def validate(self, request, visibility=MEMBER):
        params = {}
        body = request.read()
        if body and len(body):
            params = dict((k, v) for k, v in [tuple(
                map(urllib.unquote_plus, kv.split('='))
            ) for kv in body.split('&')])
        else:
            raise BLTIException('Missing or malformed parameter or value')

        try:
            launch = oauth_validate(request, params=params)
        except oauth.OAuthError as err:
            raise BLTIException(err)

        if visibility:
            self.visibility_validate(launch, visibility)

        return launch

    def visibility_validate(self, params, visibility):
        if visibility:
            roles = ','.join([params.get('roles', ''),
                              params.get('ext_roles', '')]).split(',')

            # ADMIN includes instructors, MEMBER includes
            if not (self.has_admin_role(roles) or
                    self.has_instructor_role(roles) or
                    (visibility == self.MEMBER and
                     self.has_learner_role(roles))):
                raise BLTIException(
                    'You do not have privilege to view this content.')

    def has_admin_role(self, roles):
        return self._has_role(roles, self.LIS_ADMIN)

    def has_instructor_role(self, roles):
        return self._has_role(roles, self.LIS_INSTRUCTOR)

    def has_learner_role(self, roles):
        return self._has_role(roles, self.LIS_LEARNER)

    def _has_role(self, roles, lis_roles):
        for role in roles:
            if role in lis_roles:
                return True

            m = re.match(r'^urn:lti:(inst|sys)?role:ims/lis/([A-Za-z]+)$',
                         role)
            if m and m.group(2) in lis_roles:
                return True

        return False

    def set_session(self, request, **kwargs):
        if not request.session.exists(request.session.session_key):
            request.session.create()

        kwargs['_blti_session_id'] = request.session.session_key
        request.session['blti'] = self.encrypt_session(kwargs)

    def get_session(self, request):
        if 'blti' not in request.session:
            raise BLTIException('Invalid Session')

        blti_data = self.decrypt_session(request.session['blti'])
        if blti_data['_blti_session_id'] != request.session.session_key:
            raise BLTIException('Invalid BLTI session data')

        blti_data.pop('_blti_session_id', None)
        return blti_data

    def pop_session(self, request):
        if 'blti' in request.session:
            request.session.pop('blti', None)

    def encrypt_session(self, data):
        aes = aes128cbc(settings.BLTI_AES_KEY, settings.BLTI_AES_IV)
        return b64encode(aes.encrypt(aes.pad(json.dumps(data))))

    def decrypt_session(self, string):
        aes = aes128cbc(settings.BLTI_AES_KEY, settings.BLTI_AES_IV)
        return json.loads(aes.unpad(aes.decrypt(b64decode(string))))
