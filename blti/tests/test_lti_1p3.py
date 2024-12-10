# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ImproperlyConfigured
from blti.validators import BLTIRequestValidator, Roles
from blti.models import CanvasData
from blti.roles import roles_from_role_name
from blti.performance import log_response_time
from blti import BLTI, LTI_DATA_KEY
from blti.mock_data import Mock1p3Data
from blti.exceptions import BLTIException
from oauthlib.common import generate_timestamp, generate_nonce
from urllib.parse import urlencode
import time
import mock
import os


class LTICanvasDataTest(TestCase):
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


class CanvasRolesTest(TestCase):
    def setUp(self):
        self.params = Mock1p3Data().launch_data()
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
        self._set_role('User')
        self.assertRaises(
            BLTIException, Roles(
                CanvasData(**self.params)).authorize, role='member')

        self._set_role('Administrator')
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('member'))

        self._set_role('Observer')
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('member'))

    def test_authorize_admin(self):
        self._set_role('User')
        self.assertRaises(
            BLTIException, Roles(self.launch_data).authorize, role='admin')

        self._set_role('Learner')
        self.assertRaises(
            BLTIException, Roles(
                CanvasData(**self.params)).authorize, role='admin')

        self._set_role('Administrator')
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('admin'))

        self._set_role('TeachingAssistant')
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('admin'))

        self._set_role('ContentDeveloper')
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('admin'))

        self._set_role('Student')
        self.assertRaises(
            BLTIException, Roles(
                CanvasData(**self.params)).authorize, role='admin')

    def test_authorize_specific(self):
        self._set_role('Learner')
        self.launch_data = CanvasData(**self.params)
        self.assertEquals(None, self._authorize('Learner'))

        self._set_role('ContentDeveloper')
        self.assertRaises(
            BLTIException, Roles(
                CanvasData(**self.params)).authorize, role='Instructor')

        # unknown role
        self._set_role('Learner')
        self.assertRaises(
            BLTIException, Roles(
                CanvasData(**self.params)).authorize, role='Manager')

    def _set_role(self, role):
        claim, roles = roles_from_role_name([role])
        self.params[claim] = roles


class BLTI1p3SessionTest(TestCase):
    def setUp(self):
        self.request = RequestFactory().post(
            '/test', data=Mock1p3Data().launch_data(),
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
