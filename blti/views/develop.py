# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from blti.mock_data import Mock1p3Data
from blti.roles import roles_from_role_name
from django.views.generic import TemplateView
from django.urls import reverse, resolve
from django.urls.exceptions import NoReverseMatch
from importlib import import_module
from blti import BLTIException


class BLTIDevPrepare(TemplateView):
    template_name = 'blti/develop/prepare.html'


class BLTIDevLaunch(TemplateView):
    template_name = 'blti/develop/launch.html'

    def get_context_data(self, **kwargs):
        # strategy here is to reach behind the curtain, overriding
        # the 1.3 launch auth method with call that return mock data
        role = self.request.GET.get('role', '')
        campus = self.request.GET.get('campus', '')
        mock_jwt = Mock1p3Data().launch_data()

        # insert campus
        mock_jwt["https://purl.imsglobal.org/spec/lti/claim/custom"][
            "canvas_account_sis_id"] = (
                f"uwcourse:{campus}:a-and-s:pych:psych")

        # insert role
        claim, roles = roles_from_role_name(['User', role])
        mock_jwt[claim] = roles

        launch_module, launch_class = self._launch_module_and_class()
        launch_class.validate_1p3 = lambda launch_class, request: mock_jwt

        return {
            'role': role,
            'campus': campus
        }

    def _launch_module_and_class(self):
        resolver_match = resolve(self._lti_app())
        components = resolver_match._func_path.split('.')
        launch_module = '.'.join(components[:-1])
        launch_class = components[-1]
        module = import_module(launch_module)

        return module, getattr(module, launch_class)

    def _lti_app(self):
        try:
            return reverse('lti-launch')
        except NoReverseMatch:
            raise BLTIException("Cannot find 'lti-launch' url")
