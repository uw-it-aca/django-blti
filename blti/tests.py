# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.test import RequestFactory, TestCase, override_settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ImproperlyConfigured
from blti.validators import BLTIRequestValidator, Roles
from blti.models import CanvasData
from blti.performance import log_response_time
from blti import BLTI, LTI_DATA_KEY
from blti.mock import Mock1p3Data
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


class BLTICanvasDataTest(TestCase):
    def test_known_product_code(self):
        # unimplemented product code
        data = Mock1p3Data().launch_data()
        data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"][
            "product_family_code"] = "my_lms"
        self.assertRaises(ValueError, CanvasData, **data)

    def test_attributes(self):
        data = Mock1p3Data().launch_data()
        blti = CanvasData(**data)

        self.assertEquals(blti.link_title,
                          'PSYCH 101 A Au 19, Introduction To Psychology')
        self.assertEquals(blti.return_url,
                          ("https://uw.test.instructure.com/courses/"
                           "9752574/external_content/success/"
                           "external_tool_redirect"))
        self.assertEquals(blti.canvas_course_id, '9752574')
        self.assertEquals(blti.course_sis_id, '2019-autumn-PSYCH-101-A')
        self.assertEquals(blti.course_short_name, 'PSYCH 101 A')
        self.assertEquals(blti.course_long_name,
                          'PSYCH 101 A Au 19, Introduction To Psychology')
        self.assertEquals(blti.canvas_user_id, '700007')
        self.assertEquals(blti.user_login_id, 'javerage')
        self.assertEquals(blti.user_sis_id, '0C8F043FA5CBE23F2B1E1A63B1BD80B8')
        self.assertEquals(blti.user_full_name, 'James Average')
        self.assertEquals(blti.user_first_name, 'James')
        self.assertEquals(blti.user_last_name, 'Average')
        self.assertEquals(blti.user_email, 'javerage@u.washington.edu')
        self.assertEquals(
            blti.user_avatar_url, (
                "/images/thumbnails/8140331/"
                "ynu8th19hg8afjfy1y1bnzvi4nfewe7l6tsqf7kp"))
        self.assertEquals(blti.canvas_account_id, '5171292')
        self.assertEquals(blti.account_sis_id,
                          "uwcourse:seattle:a-and-s:pych:psych")
        self.assertEquals(blti.canvas_api_domain,
                          "uw.test.instructure.com")


class Canvas1p1RolesTest(TestCase):
    def setUp(self):
        self.params = {
            "roles": 'Learner,',
            "ext_roles": ('urn:lti:instrole:ims/lis/Instructor,'
                          'urn:lti:instrole:ims/lis/Student,'
                          'urn:lti:role:ims/lis/Instructor,'
                          'urn:lti:sysrole:ims/lis/User'),
            "custom_canvas_account_sis_id":
            'uwcourse:seattle:arts-&-sciences:psych:psych',
            "oauth_timestamp": generate_timestamp(),
            "oauth_nonce": generate_nonce(),
            "resource_link_title":
            "UW LTI Development (test)",
            "oauth_consumer_key": "0000-0000-0000",
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_version": "1.0",
            "context_id": "3F2DcDcF6aCBef17a2eccCDdA498e9e5Cc333A96",
            "context_label": "PSYCH 101 A",
            "context_title": "PSYCH 101 A Au 19: Introduction To Psychology",
            "custom_application_type": "UWBLTIDevelopment",
            "custom_canvas_account_id": "8675309",
            "custom_canvas_api_domain": "uw.test.instructure.com",
            "custom_canvas_course_id": "88675309",
            "custom_canvas_enrollment_state": "active",
            "custom_canvas_user_id": "700007",
            "custom_canvas_user_login_id": "javerage",
            "custom_canvas_workflow_state": "available",
            "launch_presentation_document_target": "iframe",
            "launch_presentation_height": "400",
            "launch_presentation_locale": "en",
            "launch_presentation_width": "800",
            "lis_course_offering_sourcedid": "2019-autumn-PSYCH-101-A",
            "lis_person_contact_email_primary": "javerage@u.washington.edu",
            "lis_person_name_family": "Average",
            "lis_person_name_full": "James Average",
            "lis_person_name_given": "James",
            "lis_person_sourcedid": "0C8F043FA5CBE23F2B1E1A63B1BD80B8",
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "oauth_callback": "about:blank",
            "resource_link_id": "E9a206DC909a330e9F8eF183b7BB4B9718aBB62d",
            "tool_consumer_info_product_family_code": "canvas",
            "tool_consumer_instance_name": "University of Washington",
            "user_id": "e1ec31bd10a32f61dd65975ce4eb98e9f106bd7d",
            "user_image": ('/images/thumbnails/1499380/'
                           '24ZSCuR73P2mrG98Yq6gicMHjcd0p8NMhM2iGhgz'),
        }

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


class BLTILaunchViewTest(TestCase):
    def test_launch_view(self):
        self.assertRaises(NoReverseMatch, reverse, 'lti-launch')


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
