# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.db import models


CLAIM_LIS = 'https://purl.imsglobal.org/spec/lti/claim/lis'
CLAIM_CUSTOM = 'https://purl.imsglobal.org/spec/lti/claim/custom'
CLAIM_CONTEXT = 'https://purl.imsglobal.org/spec/lti/claim/context'
CLAIM_LINK = 'https://purl.imsglobal.org/spec/lti/claim/resource_link'


class BLTIData(object):
    def __init__(self, **kwargs):
        self.data = kwargs

        # Canvas internal IDs
        self.canvas_course_id = kwargs.get('custom_canvas_course_id')
        self.canvas_user_id = kwargs.get('custom_canvas_user_id')
        self.canvas_account_id = kwargs.get(
            'custom_canvas_account_id',
            self._custom('canvas_account_id'))

        # SIS IDs
        self.course_sis_id = kwargs.get(
            'lis_course_offering_sourcedid',
            self._lis('course_offering_sourcedid'))
        self.user_sis_id = kwargs.get(
            'lis_person_sourcedid',
            self._lis('person_sourcedid'))
        self.account_sis_id = kwargs.get(
            'custom_canvas_account_sis_id',
            self._custom('canvas_account_sis_id'))

        # Course attributes
        self.course_short_name = kwargs.get(
            'context_label', self._context('label'))
        self.course_long_name = kwargs.get(
            'context_title', self._context('title'))

        # User attributes
        self.user_login_id = kwargs.get(
            'custom_canvas_user_login_id', self._custom('canvas_login_id'))
        self.user_full_name = kwargs.get(
            'lis_person_name_full', self.data.get('name'))
        self.user_first_name = kwargs.get(
            'lis_person_name_given', self.data.get('given_name'))
        self.user_last_name = kwargs.get(
            'lis_person_name_family', self.data.get('family_name'))
        self.user_email = kwargs.get(
            'lis_person_contact_email_primary')
        self.user_avatar_url = kwargs.get(
            'user_image', self.data.get('picture'))

        # LTI app attributes
        self.link_title = kwargs.get(
            'resource_link_title', self._link('title'))
        self.return_url = kwargs.get('launch_presentation_return_url')

        # Canvas hostname
        self.canvas_api_domain = kwargs.get('custom_canvas_api_domain')

    def _lis(self, key):
        return self._data_claim(CLAIM_LIS, key)

    def _custom(self, key):
        return self._data_claim(CLAIM_CUSTOM, key)

    def _context(self, key):
        return self._data_claim(CLAIM_CONTEXT, key)

    def _link(self, key):
        return self._data_claim(CLAIM_LINK, key)

    def _data_claim(self, claim, key):
        return self.data.get(claim, {}).get(key)

    def get(self, name):
        return self.data.get(name)
