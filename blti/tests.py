from django.test import TestCase
from blti.validators import *
from blti.crypto import aes128cbc
from blti import BLTIException


class BLTIOAuthTest(TestCase):
    def test_get_consumer(self):
        with self.settings(LTI_CONSUMERS={'ABC': '12345'}):
            self.assertEquals(BLTIOauth().get_consumer('ABC').secret, '12345')
            self.assertEquals(None, BLTIOauth().get_consumer('XYZ'))


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
