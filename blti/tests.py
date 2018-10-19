from django.conf import settings
from django.test import RequestFactory, TestCase
from blti.validators import BLTIRequestValidator, Roles
from blti.crypto import aes128cbc
from blti.models import BLTIData
from blti import BLTI, BLTIException
import time


class RequestValidatorTest(TestCase):
    def setUp(self):
        self.request = RequestFactory().post(
            '/test', data=getattr(settings, 'CANVAS_LTI_V1_LAUNCH_PARAMS', {}),
            secure=True)

    def test_check_client_key(self):
        self.assertTrue(BLTIRequestValidator().check_client_key('x' * 12))
        self.assertTrue(BLTIRequestValidator().check_client_key('5' * 30))
        self.assertTrue(BLTIRequestValidator().check_client_key('-' * 20))
        self.assertTrue(BLTIRequestValidator().check_client_key('_' * 20))
        self.assertFalse(BLTIRequestValidator().check_client_key('x' * 11))
        self.assertFalse(BLTIRequestValidator().check_client_key('x' * 31))
        self.assertFalse(BLTIRequestValidator().check_client_key('*' * 40))

    def test_check_nonce(self):
        self.assertTrue(BLTIRequestValidator().check_nonce('x' * 20))
        self.assertTrue(BLTIRequestValidator().check_nonce('5' * 50))
        self.assertTrue(BLTIRequestValidator().check_nonce('-' * 20))
        self.assertTrue(BLTIRequestValidator().check_nonce('_' * 20))
        self.assertFalse(BLTIRequestValidator().check_nonce('*' * 20))
        self.assertFalse(BLTIRequestValidator().check_nonce('x' * 19))
        self.assertFalse(BLTIRequestValidator().check_nonce('x' * 51))

    def test_validate_client_key(self):
        with self.settings(LTI_CONSUMERS={}):
            self.assertFalse(
                BLTIRequestValidator().validate_client_key('X', self.request))

        with self.settings(LTI_CONSUMERS={'A': '12345'}):
            self.assertTrue(
                BLTIRequestValidator().validate_client_key('A', self.request))

    def test_get_client_secret(self):
        with self.settings(LTI_CONSUMERS={}):
            self.assertEquals(
                BLTIRequestValidator().get_client_secret('X', self.request),
                'dummy')

        with self.settings(LTI_CONSUMERS={'A': '12345'}):
            self.assertEquals(
                BLTIRequestValidator().get_client_secret('A', self.request),
                '12345')

    def test_validate_timestamp_and_nonce(self):
        self.assertTrue(
            BLTIRequestValidator().validate_timestamp_and_nonce(
                'X', time.time(), '', self.request))

        self.assertFalse(
            BLTIRequestValidator().validate_timestamp_and_nonce(
                'X', time.time() - 65, '', self.request))

        self.assertFalse(
            BLTIRequestValidator().validate_timestamp_and_nonce(
                'X', time.time() + 65, '', self.request))

        self.assertFalse(
            BLTIRequestValidator().validate_timestamp_and_nonce(
                'X', '1234567890', '', self.request))


class BLTIDataTest(TestCase):
    def test_attributes(self):
        params = getattr(settings, 'CANVAS_LTI_V1_LAUNCH_PARAMS', {})
        blti = BLTIData(**params)

        self.assertEquals(blti.link_title, 'Example App')
        self.assertEquals(blti.return_url,
                          'https://example.instructure.com/courses/123456')
        self.assertEquals(blti.canvas_course_id, '123456')
        self.assertEquals(blti.course_sis_id, '2018-spring-ABC-101-A')
        self.assertEquals(blti.course_short_name, 'ABC 101 A')
        self.assertEquals(blti.course_long_name, 'ABC 101 A: Example Course')
        self.assertEquals(blti.canvas_user_id, '123456')
        self.assertEquals(blti.user_login_id, 'javerage')
        self.assertEquals(blti.user_sis_id, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        self.assertEquals(blti.user_full_name, 'James Average')
        self.assertEquals(blti.user_first_name, 'James')
        self.assertEquals(blti.user_last_name, 'Average')
        self.assertEquals(blti.user_email, 'javerage@example.edu')
        self.assertEquals(
            blti.user_avatar_url, (
                'https://example.instructure.com/images/thumbnails/123456/'
                'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'))
        self.assertEquals(blti.canvas_account_id, '12345')
        self.assertEquals(blti.account_sis_id, 'example:account')
        self.assertEquals(blti.canvas_api_domain, 'example.instructure.com')

    def test_get(self):
        params = getattr(settings, 'CANVAS_LTI_V1_LAUNCH_PARAMS', {})
        blti = BLTIData(**params)

        self.assertEquals(blti.get('custom_canvas_course_id'), '123456')
        self.assertEquals(blti.get('lis_person_contact_email_primary'),
                          'javerage@example.edu')
        self.assertEquals(blti.get('invalid_param_name'), None)


class CanvasRolesTest(TestCase):
    def setUp(self):
        params = {
            'tool_consumer_info_product_family_code': 'canvas',
            'roles': '',
            'ext_roles': ''
        }
        self.blti = BLTIData(**params)

    def test_authorize_nodata(self):
        # no blti object
        self.assertRaises(
            BLTIException, Roles().authorize, None, role='member')

        # unimplemented product code
        self.blti.data['tool_consumer_info_product_family_code'] = 'my_lms'
        self.assertRaises(
            BLTIException, Roles().authorize, self.blti, role='member')

    def test_authorize_public(self):
        self.assertEquals(None, Roles().authorize(self.blti, role='public'))
        self.assertEquals(None, Roles().authorize(self.blti, role=None))

    def test_authorize_member(self):
        self.assertRaises(
            BLTIException, Roles().authorize, self.blti, role='member')

        self.blti.data['roles'] = 'Administrator'
        self.assertEquals(None, Roles().authorize(self.blti, role='member'))

        self.blti.data['roles'] = 'urn:lti:instrole:ims/lis/Observer'
        self.assertEquals(None, Roles().authorize(self.blti, role='member'))

    def test_authorize_admin(self):
        self.assertRaises(
            BLTIException, Roles().authorize, self.blti, role='admin')

        self.blti.data['roles'] = 'Learner'
        self.assertRaises(
            BLTIException, Roles().authorize, self.blti, role='admin')

        self.blti.data['roles'] = 'urn:lti:instrole:ims/lis/Administrator'
        self.assertEquals(None, Roles().authorize(self.blti, role='admin'))

        self.blti.data['roles'] = 'urn:lti:role:ims/lis/TeachingAssistant'
        self.assertEquals(None, Roles().authorize(self.blti, role='admin'))

        self.blti.data['roles'] = 'Learner,ContentDeveloper'
        self.assertEquals(None, Roles().authorize(self.blti, role='admin'))

        # ignores ext_roles
        self.blti.data['roles'] = 'Learner'
        self.blti.data['ext_roles'] = 'urn:lti:role:ims/lis/Instructor'
        self.assertRaises(
            BLTIException, Roles().authorize, self.blti, role='admin')

    def test_authorize_specific(self):
        self.blti.data['roles'] = 'Learner'
        self.assertEquals(None, Roles().authorize(self.blti, role='Learner'))

        self.blti.data['roles'] = 'urn:lti:role:ims/lis/Learner'
        self.assertEquals(None, Roles().authorize(self.blti, role='Learner'))

        self.blti.data['roles'] = 'Learner,ContentDeveloper'
        self.assertRaises(
            BLTIException, Roles().authorize, self.blti, role='Instructor')

        # unknown role
        self.blti.data['roles'] = 'Learner'
        self.assertRaises(
            BLTIException, Roles().authorize, self.blti, role='Manager')


class BLTISessionTest(TestCase):
    def test_encrypt_decrypt_session(self):
        with self.settings(BLTI_AES_KEY='DUMMY_KEY_FOR_TESTING_1234567890',
                           BLTI_AES_IV='DUMMY_IV_TESTING'):

            data = {'abc': {'key': 123},
                    'xyz': ('LTI provides a framework through which an LMS '
                            'can send some verifiable information about a '
                            'user to a third party.')}

            enc = BLTI()._encrypt_session(data)
            self.assertEquals(BLTI()._decrypt_session(enc), data)

    def test_filter_oauth_params(self):
        with self.settings(BLTI_AES_KEY='DUMMY_KEY_FOR_TESTING_1234567890',
                           BLTI_AES_IV='DUMMY_IV_TESTING'):
            data = getattr(settings, 'CANVAS_LTI_V1_LAUNCH_PARAMS', {})

            self.assertEquals(len(data), 43)
            self.assertEquals(data['oauth_consumer_key'], 'XXXXXXXXXXXXXX')

            data = BLTI().filter_oauth_params(data)
            self.assertEquals(len(data), 36)
            self.assertRaises(KeyError, lambda: data['oauth_consumer_key'])
