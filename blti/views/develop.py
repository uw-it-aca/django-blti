# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.views.generic import TemplateView
from django.urls import reverse, resolve
from django.urls.exceptions import NoReverseMatch
from importlib import resources, import_module
from blti import BLTIException
import json
import os


MOCK_JWT_FILE = ('resources', 'lti1p3', 'file', 'jwt.json')


class BLTIDevPrepare(TemplateView):
    template_name = 'blti/develop/prepare.html'


class BLTIDevLaunch(TemplateView):
    template_name = 'blti/develop/launch.html'

    def get_context_data(self, **kwargs):
        # strategy here is to reach behind the curtain, overriding
        # the 1.3 launch auth method with call that return mock data
        role = self.request.GET.get('role', '')
        campus = self.request.GET.get('campus', '')
        mock_jwt = self.get_lti1p3_jwt()

        # insert campus
        mock_jwt["https://purl.imsglobal.org/spec/lti/claim/custom"][
            "canvas_account_sis_id"] = (
                f"uwcourse:{campus}:a-and-s:pych:psych")

        # insert role
        role_base = "http://purl.imsglobal.org/vocab/lis/v2"
        roles = [f"{role_base}system/person#User"]
        if role == "Instructor":
            roles += [f"{role_base}/institution/person#Instructor",
                      f"{role_base}/membership#Instructor"]
        elif role == "TeachingAssistant":
            roles += [f"{role_base}/membership#TeachingAssistant"]
        elif role ==  "Student":
            roles += [f"{role_base}/institution/person#Student",
                      f"{role_base}/membership#Learner"]
        elif role ==  "Administrator":
            roles += [f"{role_base}/system/person#Administrator"]
        elif role ==  "ContentDeveloper":
            roles += [f"{role_base}/membership#ContentDeveloper"]

        mock_jwt["https://purl.imsglobal.org/spec/lti/claim/roles"] = roles

        launch_module, launch_class = self._launch_module_and_class()
        launch_class.validate_1p3 = lambda launch_class, request: mock_jwt

        return {
            'role': role,
            'campus': campus
        }

    def _launch_module_and_class(self):
        resolver_match = resolve(self.lti_app())
        components = resolver_match._func_path.split('.')
        launch_module = '.'.join(components[:-1])
        launch_class = components[-1]
        module = import_module(launch_module)

        return module, getattr(module, launch_class)

    def get_lti1p3_jwt(self):
        mock_jwt_file = os.path.join(*MOCK_JWT_FILE)
        mock_jwt_path = os.path.join(
            resources.files('blti'), mock_jwt_file)

        for app in settings.INSTALLED_APPS:
            try:
                path = os.path.join(resources.files(app), mock_jwt_file)
            except Exception:
                continue

            if path != mock_jwt_path and os.path.exists(path):
                mock_jwt_path = path
                break

        with open(mock_jwt_path, 'r') as f:
            return json.load(f)

    def lti_app(self):
        try:
            return reverse('lti-launch')
        except NoReverseMatch:
            raise BLTIException("Cannot find 'lti-launch' url")
