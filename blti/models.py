# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.db import models


CLAIM_LIS = 'https://purl.imsglobal.org/spec/lti/claim/lis'
CLAIM_CUSTOM = 'https://purl.imsglobal.org/spec/lti/claim/custom'
CLAIM_CONTEXT = 'https://purl.imsglobal.org/spec/lti/claim/context'
CLAIM_LINK = 'https://purl.imsglobal.org/spec/lti/claim/resource_link'


class BLTIData(object):
    def __init__(self, **data):
        # Canvas internal IDs
        self.canvas_course_id = data.get('custom_canvas_course_id')
        self.canvas_user_id = data.get('custom_canvas_user_id')
        self.canvas_account_id = data.get(
            'custom_canvas_account_id',
            self._custom(data, 'canvas_account_id'))

        # SIS IDs
        self.course_sis_id = data.get(
            'lis_course_offering_sourcedid',
            self._lis(data, 'course_offering_sourcedid'))
        self.user_sis_id = data.get(
            'lis_person_sourcedid',
            self._lis(data, 'person_sourcedid'))
        self.account_sis_id = data.get(
            'custom_canvas_account_sis_id',
            self._custom(data, 'canvas_account_sis_id'))

        # Course attributes
        self.course_short_name = data.get(
            'context_label', self._context(data, 'label'))
        self.course_long_name = data.get(
            'context_title', self._context(data, 'title'))

        # User attributes
        self.user_login_id = data.get(
            'custom_canvas_user_login_id',
            self._custom(data, 'canvas_login_id'))
        self.user_full_name = data.get(
            'lis_person_name_full', data.get('name'))
        self.user_first_name = data.get(
            'lis_person_name_given', data.get('given_name'))
        self.user_last_name = data.get(
            'lis_person_name_family', data.get('family_name'))
        self.user_email = data.get(
            'lis_person_contact_email_primary')
        self.user_avatar_url = data.get(
            'user_image', data.get('picture'))

        # LTI app attributes
        self.link_title = data.get(
            'resource_link_title', self._link(data, 'title'))
        self.return_url = data.get('launch_presentation_return_url')

        # Canvas hostname
        self.canvas_api_domain = data.get('custom_canvas_api_domain')

    def _lis(self, data, key):
        return self._data_claim(CLAIM_LIS, data, key)

    def _custom(self, data, key):
        return self._data_claim(CLAIM_CUSTOM, data, key)

    def _context(self, data, key):
        return self._data_claim(CLAIM_CONTEXT, data, key)

    def _link(self, data, key):
        return self._data_claim(CLAIM_LINK, data, key)

    def _data_claim(self, claim, data, key):
        return data.get(claim, {}).get(key)
