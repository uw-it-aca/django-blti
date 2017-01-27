from django.test import TestCase
from blti.validators import *
from blti.crypto import aes128cbc
from blti import BLTIException


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
    msg = ('LTI provides a framework through which an LMS can send some '
           'verifiable information about a user to a third party.')
    padded = ('LTI provides a framework through which an LMS can send '
              'some verifiable information about a user to a third party.'
              '\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f')
    encrypted = ('\xff\xf7\xe1\xed\xeen\xd3\x1a\x01\xe9\xd2\x06\xf7\x14v!'
                 '\xbf\xe5\x11\x0e+\xa6\xf5\xf8\xe7\xc8\xcd\xae\xf6;j$\x00'
                 '\x9c#\xc1\xa7\x1cz;\xcdp\x97\x86\xbef\x9fl\xfb\xbcz\x9eP'
                 '\x91\xa4RltA\xe8\xf1\rb\xbd.+\x97\x8b\xf1\xc9<?7\xabF/'
                 '\x0e\xef\xd7\xc7y\xcb\xbd\x9c\xb7\xa0\x95\x0ciKI\xe1\x08'
                 '\xf7\x1a\x90c\xf1\x7f\xe4\x93\xb11=\xd6\xe2\xc1G\xd15\x05'
                 '\x1b\xab\x07\x1c\xf6H\n\xaa3\xc6\x01H\xcc\xea\xbeh\xd5')

    def test_encrypt(self):
        aes = aes128cbc(self.test_key, self.test_iv)
        self.assertEquals(aes.encrypt(aes.pad(self.msg)), self.encrypted)

    def test_decrypt(self):
        aes = aes128cbc(self.test_key, self.test_iv)
        self.assertEquals(aes.unpad(aes.decrypt(self.encrypted)), self.msg)

    def test_pad(self):
        aes = aes128cbc(self.test_key, self.test_iv)
        self.assertEquals(aes.pad(self.msg), self.padded)

    def test_unpad(self):
        aes = aes128cbc(self.test_key, self.test_iv)
        self.assertEquals(aes.unpad(self.padded), self.msg)
