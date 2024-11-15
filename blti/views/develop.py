# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.views.generic import TemplateView
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from oauthlib.common import generate_timestamp, generate_nonce
from oauthlib.oauth1.rfc5849 import Client
from oauthlib.oauth1.rfc5849.signature import (
    base_string_uri, signature_base_string,
    normalize_parameters, sign_hmac_sha1_with_client)
from importlib import resources
from blti import BLTIException
import json
import re
import os


class BLTIDevBase(TemplateView):
    def lti_app(self):
        try:
            return reverse('lti-launch')
        except NoReverseMatch:
            raise BLTIException("Cannot find 'lti-launch' url")

    def lti_app_uri(self):
        blti_match = re.match(r'^(http[s]?://[^/?]+)/.*',
                              self.request.build_absolute_uri())
        return "{}{}".format(blti_match.group(1), self.lti_app()[:-1])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lti_app'] = self.lti_app()
        return context


class BLTIDevPrepare(BLTIDevBase):
    template_name = 'blti/develop/prepare.html'


class BLTIDevLaunch(BLTIDevBase):
    template_name = 'blti/develop/launch.html'

    # well known dev client
    _client_key = '0000-0000-0000'
    _client_secrets = getattr(
        settings, 'LTI_CONSUMERS', {'0000-0000-0000': '01234567ABCDEF'})

    _lti_role = {
        'administrator': 'urn:lti:instrole:ims/lis/Administrator',
        'instructor': 'Instructor',
        'ta': 'urn:lti:role:ims/lis/TeachingAssistant',
        'student': 'Learner,'
    }

    _lti_ext_role = {
        'administrator': 'urn:lti:instrole:ims/lis/Administrator,'
        + 'urn:lti:instrole:ims/lis/Instructor,'
        + 'urn:lti:instrole:ims/lis/Student,'
        + 'urn:lti:role:ims/lis/Learner,'
        + 'urn:lti:role:ims/lis/Learner/NonCreditLearner,'
        + 'urn:lti:role:ims/lis/Mentor,'
        + 'urn:lti:sysrole:ims/lis/Useurn:lti:'
        + 'instrole:ims/lis/Administrator,'
        + 'urn:lti:instrole:ims/lis/Instructor,'
        + 'urn:lti:instrole:ims/lis/Student,urn:lti:role:ims/lis/Learner,'
        + 'urn:lti:role:ims/lis/Learner/NonCreditLearner,'
        + 'urn:lti:role:ims/lis/Mentor,'
        + 'urn:lti:sysrole:ims/lis/User',
        'instructor': 'urn:lti:instrole:ims/lis/Instructor,'
        + 'urn:lti:instrole:ims/lis/Student,'
        + 'urn:lti:role:ims/lis/Instructor,'
        + 'urn:lti:sysrole:ims/lis/User',
        'ta': 'urn:lti:instrole:ims/lis/Instructor,'
        + 'urn:lti:instrole:ims/lis/Student,'
        + 'urn:lti:role:ims/lis/Instructor,'
        + 'urn:lti:role:ims/lis/TeachingAssistant,'
        + 'urn:lti:sysrole:ims/lis/User',
        'student': 'urn:lti:instrole:ims/lis/Student,'
        + 'urn:lti:role:ims/lis/Learner,urn:lti:sysrole:ims/lis/User'
    }

    _static_oauth_lti_parameters = [
        ("oauth_consumer_key", "0000-0000-0000"),
        ("oauth_signature_method", "HMAC-SHA1"),
        ("oauth_version", "1.0"),
    ]
    _static_lti_parameters = [
        ("context_id", "3F2DcDcF6aCBef17a2eccCDdA498e9e5Cc333A96"),
        ("custom_application_type", "UWBLTIDevelopment"),
        ("custom_canvas_account_id", "8675309"),
        ("custom_canvas_api_domain", "uw.test.instructure.com"),
        ("custom_canvas_course_id", "88675309"),
        ("launch_presentation_document_target", "iframe"),
        ("launch_presentation_height", "400"),
        ("launch_presentation_locale", "en"),
        ("launch_presentation_width", "800"),
        ("lti_message_type", "basic-lti-launch-request"),
        ("lti_version", "LTI-1p0"),
        ("oauth_callback", "about:blank"),
        ("resource_link_id", "E9a206DC909a330e9F8eF183b7BB4B9718aBB62d"),
        ("tool_consumer_info_product_family_code", "canvas"),
        ("tool_consumer_instance_name", "University of Washington"),
        ("user_id", "e1ec31bd10a32f61dd65975ce4eb98e9f106bd7d"),
        ("user_image", '/images/thumbnails/1499380/'
         + '24ZSCuR73P2mrG98Yq6gicMHjcd0p8NMhM2iGhgz'),
    ]

    def get_course_parameters(self):
        parameters = []
        mock_parameter_path = os.path.join(
            resources.files('blti'), 'resources',
            'lti1p1', 'course_parameters.json')

        for app in settings.INSTALLED_APPS:
            try:
                path = os.path.join(resources.files(app), 'resources',
                                    'lti1p1', 'course_parameters.json')
            except Exception:
                continue

            if path != mock_parameter_path and os.path.exists(path):
                mock_parameter_path = path
                break

        with open(mock_parameter_path, 'r') as f:
            for k, v in json.load(f):
                parameters.append((k, v))

        return parameters

    def get_context_data(self, **kwargs):
        role = self.request.GET.get('role', '')
        campus = self.request.GET.get('campus', '')

        lti_parameters = [
            ("roles", self._lti_role[role]),
            ("ext_roles", self._lti_ext_role[role]),
            ("custom_canvas_account_sis_id",
             'uwcourse:{}:arts-&-sciences:psych:psych'.format(campus)),
            ("oauth_timestamp", generate_timestamp()),
            ("oauth_nonce", generate_nonce()),
            ("resource_link_title",
             "UW LTI Development ({})".format(self.lti_app())),
        ] + self._static_oauth_lti_parameters + sorted(
            self._static_lti_parameters + self.get_course_parameters(),
            key=lambda x: x[0])

        # sign payload
        lti_app_uri = self.lti_app_uri()
        sbs = signature_base_string('POST',
                                    base_string_uri(lti_app_uri + '/'),
                                    normalize_parameters(lti_parameters))
        client_key = self._client_key
        client = Client(
            client_key, client_secret=self._client_secrets[client_key])
        signature = sign_hmac_sha1_with_client(sbs, client)
        lti_parameters.append(("oauth_signature", signature))

        context = super().get_context_data(**kwargs)
        context['uri'] = lti_app_uri
        context['campus'] = campus
        context['role_name'] = role
        context['lti_parameters'] = lti_parameters
        return context
