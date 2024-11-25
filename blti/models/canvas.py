# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from .base import LTILaunchData


class CanvasData(LTILaunchData):
    def __init__(self, **data):
        super(CanvasData, self).__init__(**data)

        if self.platform_name != 'canvas':
            raise ValueError('This is not a Canvas LTI launch')

        # Canvas internal IDs
        self.canvas_course_id = self.claim_custom('canvas_course_id')
        self.canvas_user_id = self.claim_custom('canvas_user_id')
        self.canvas_account_id = self.claim_custom('canvas_account_id')

        # SIS IDs
        self.course_sis_id = self.claim_lis('course_offering_sourcedid')
        self.user_sis_id = self.claim_lis('person_sourcedid')
        self.account_sis_id = self.claim_custom('canvas_account_sis_id')

        # Course attributes
        self.course_short_name = self.claim_context('label')
        self.course_long_name = self.claim_context('title')

        # User attributes
        self.user_login_id = self.claim_custom('canvas_user_login_id')
        self.user_full_name = data.get(
            'lis_person_name_full', data.get('name'))
        self.user_first_name = data.get(
            'lis_person_name_given', data.get('given_name'))
        self.user_last_name = data.get(
            'lis_person_name_family', data.get('family_name'))
        self.user_email = data.get(
            'lis_person_contact_email_primary', data.get('email'))
        self.user_avatar_url = data.get(
            'user_image', data.get('picture'))

        # LTI app attributes
        self.link_title = self.claim_resource_link('title')
        self.return_url = self.claim_launch_presentation('return_url')

        # Canvas hostname
        self.canvas_api_domain = self.claim_custom('canvas_api_domain')
