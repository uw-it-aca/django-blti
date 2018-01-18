from django.conf import settings
from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from blti.validators import BLTIOauth, Roles
from blti.crypto import aes128cbc
from blti.models import BLTIData
from blti import BLTI, BLTIException


class BLTIOAuthTest(TestCase):
    def test_no_config(self):
        self.assertRaises(ImproperlyConfigured, BLTIOauth)

    def test_no_consumer(self):
        with self.settings(LTI_CONSUMERS={}):
            self.assertRaises(BLTIException, BLTIOauth().get_consumer, 'XYZ')

        with self.settings(LTI_CONSUMERS={'ABC': '12345'}):
            self.assertRaises(BLTIException, BLTIOauth().get_consumer, 'XYZ')

    def test_get_consumer(self):
        with self.settings(LTI_CONSUMERS={'ABC': '12345'}):
            self.assertEquals(BLTIOauth().get_consumer('ABC').secret, '12345')


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


class CryptoTest(TestCase):
    test_key = 'DUMMY_KEY_FOR_TESTING_1234567890'
    test_iv = 'DUMMY_IV_TESTING'
    msgs = [
        ('LTI provides a framework through which an LMS can send some '
         'verifiable information about a user to a third party.'),
        "'abc': {'key': value}"
    ]

    def test_encrypt_decrypt(self):
        aes = aes128cbc(self.test_key, self.test_iv)

        for msg in self.msgs:
            enc = aes.encrypt(msg)
            self.assertEquals(aes.decrypt(enc), msg)
