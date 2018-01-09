from django.conf import settings
from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from blti.validators import BLTIOauth, BLTIRoles
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


class BLTIRolesTest(TestCase):
    def test_has_admin_role(self):
        self.assertEquals(
            True, BLTIRoles().has_admin_role(['Faculty', 'Alumni']))
        self.assertEquals(False, BLTIRoles().has_admin_role(['Guest']))

    def test_has_instructor_role(self):
        self.assertEquals(
            True, BLTIRoles().has_instructor_role(['TeachingAssistant']))
        self.assertEquals(
            False, BLTIRoles().has_instructor_role(['Faculty', 'Alumni']))

    def test_has_learner_role(self):
        self.assertEquals(
            True, BLTIRoles().has_learner_role(['Member']))
        self.assertEquals(
            False, BLTIRoles().has_learner_role(['Faculty', 'Staff']))

    def test_validate(self):
        blti = None
        self.assertRaises(
            BLTIException, BLTIRoles().validate, blti, 'member')

        blti = {'roles': 'Member'}
        self.assertEquals(None, BLTIRoles().validate(blti, 'member'))
        self.assertRaises(
            BLTIException, BLTIRoles().validate, blti, 'admin')

        blti = {'roles': 'Faculty,Staff'}
        self.assertEquals(None, BLTIRoles().validate(blti, 'member'))
        self.assertEquals(None, BLTIRoles().validate(blti, 'admin'))


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
