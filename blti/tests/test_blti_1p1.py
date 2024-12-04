# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ImproperlyConfigured
from blti.models import CanvasData
from blti.validators import BLTIRequestValidator, Roles
from blti.performance import log_response_time
from blti import BLTI, LTI_DATA_KEY
from blti.mock_data import Mock1p3Data
from blti.exceptions import BLTIException
from oauthlib.common import generate_timestamp, generate_nonce
from urllib.parse import urlencode
import time
import mock
import os


class RequestValidator1p1Test(TestCase):
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


class CanvasRolesTest(TestCase):
    def setUp(self):
        self.params = getattr(settings, 'CANVAS_LTI_V1_LAUNCH_PARAMS', {})
        self.launch_data = CanvasData(**self.params)

    def _authorize(self, role):
        return Roles(self.launch_data).authorize(role=role)

    def test_authorize_nodata(self):
        # no blti object
        self.assertRaises(
            ImproperlyConfigured, Roles(None).authorize, role='member')

    def test_authorize_public(self):
        self.assertEquals(None, self._authorize('public'))
        self.assertEquals(None, self._authorize(None))

    def test_authorize_member(self):
        self.params['roles'] = 'User'
        self.assertRaises(
            BLTIException, Roles(
                CanvasData(**self.params)).authorize, role='member')

        self.params['roles'] = 'Administrator'
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('member'))

        self.params['roles'] = 'urn:lti:instrole:ims/lis/Observer'
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('member'))

    def test_authorize_admin(self):
        self.assertRaises(
            BLTIException, Roles(self.launch_data).authorize, role='admin')

        self.params['roles'] = 'Learner'
        self.assertRaises(
            BLTIException, Roles(
                CanvasData(**self.params)).authorize, role='admin')

        self.params['roles'] = 'urn:lti:instrole:ims/lis/Administrator'
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('admin'))

        self.params['roles'] = 'urn:lti:role:ims/lis/TeachingAssistant'
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('admin'))

        self.params['roles'] = 'Learner,ContentDeveloper'
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('admin'))

        # ignores ext_roles
        self.params['roles'] = 'Learner'
        self.params['ext_roles'] = 'urn:lti:role:ims/lis/Instructor'
        self.assertRaises(
            BLTIException, Roles(
                CanvasData(**self.params)).authorize, role='admin')

    def test_authorize_specific(self):
        self.params['roles'] = 'Learner'
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('Learner'))

        self.params['roles'] = 'urn:lti:role:ims/lis/Learner'
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('Learner'))

        self.params['roles'] = 'Learner,ContentDeveloper'
        self.assertRaises(
            BLTIException, Roles(
                CanvasData(**self.params)).authorize, role='Instructor')

        # unknown role
        self.params['roles'] = 'Learner'
        self.assertRaises(
            BLTIException, Roles(
                CanvasData(**self.params)).authorize, role='Manager')


class BLTI1p1SessionTest(TestCase):
    def setUp(self):
        self.request = RequestFactory().post(
            '/test', data=getattr(settings, 'CANVAS_LTI_V1_LAUNCH_PARAMS', {}),
            secure=True)
        SessionMiddleware(get_response=mock.MagicMock()).process_request(
            self.request)

    def test_set_session(self):
        blti = BLTI()
        self.assertFalse(LTI_DATA_KEY in self.request.session)
        blti.set_session(self.request)
        self.assertTrue(LTI_DATA_KEY in self.request.session)

    def test_get_session(self):
        blti = BLTI()
        self.assertRaises(BLTIException, blti.get_session, self.request)

        blti.set_session(self.request)
        self.assertEqual(blti.get_session(self.request), {})

    def test_filter_oauth_params(self):
        data = getattr(settings, 'CANVAS_LTI_V1_LAUNCH_PARAMS', {})

        self.assertEquals(len(data), 43)
        self.assertEquals(data['oauth_consumer_key'], 'XXXXXXXXXXXXXX')

        blti = BLTI()
        blti.set_session(self.request, **data)
        blti_data = blti.get_session(self.request)
        self.assertEquals(len(blti_data), 36)
        self.assertRaises(KeyError, lambda: blti_data['oauth_consumer_key'])


class BLTIDecoratorTest(TestCase):
    def setUp(self):
        self.request = RequestFactory().post(
            '/test', data=getattr(settings, 'CANVAS_LTI_V1_LAUNCH_PARAMS', {}),
            secure=True)
        SessionMiddleware(get_response=mock.MagicMock()).process_request(
            self.request)

    def test_log_response_time(self):
        func = mock.Mock()
        func.__name__ = 'test'
        decorated_func = log_response_time(func)

        with self.assertLogs(level='INFO') as cm:
            response = decorated_func(self.request, 'test1', test_id=123)

        self.assertIn(
            'INFO:blti.performance:user: None, method: '
            'django.core.handlers.wsgi.test, args: (\'test1\',), '
            'kwargs: {\'test_id\': 123}, time: ',
            cm.output[0])