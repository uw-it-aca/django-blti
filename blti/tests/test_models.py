# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.test import TestCase
from blti.models.canvas import CanvasData
import os
import json


class TestCanvasModel(TestCase):
    def get_launch_jwt(self):
        jwt_file_path = '../resources/lti1p3/file/jwt.json'
        jwt_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), jwt_file_path))
        with open(jwt_file) as f:
            return json.load(f)

    def test_canvas_model(self):
        jwt = self.get_launch_jwt()
        blti_data = CanvasData(**jwt)
        self.assertEqual(blti_data.canvas_user_id, '700007')
        self.assertEqual(
            blti_data.user_sis_id, '0C8F043FA5CBE23F2B1E1A63B1BD80B8')
        self.assertEqual(blti_data.course_sis_id, '2019-autumn-PSYCH-101-A')

    def test_canvas_model_unset_course_sis_id(self):
        jwt = self.get_launch_jwt()

        jwt['https://purl.imsglobal.org/spec/lti/claim/lis'][
            'course_offering_sourcedid'] = '$CanvasSectionSISID'

        blti_data = CanvasData(**jwt)
        self.assertEqual(blti_data.canvas_user_id, '700007')
        self.assertEqual(
            blti_data.user_sis_id, '0C8F043FA5CBE23F2B1E1A63B1BD80B8')
        self.assertIsNone(blti_data.course_sis_id)
