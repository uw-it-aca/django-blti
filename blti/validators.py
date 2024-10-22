# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from blti.exceptions import BLTIException
import time
import re


class Roles(object):
    # https://www.imsglobal.org/specs/ltiv1p1/implementation-guide#toc-30
    CANVAS_ROLES = {
        'member': ['Administrator', 'Instructor', 'TeachingAssistant',
                   'ContentDeveloper', 'Learner', 'Observer'],
        'admin': ['Administrator', 'Instructor', 'TeachingAssistant',
                  'ContentDeveloper'],
    }

    RE_ROLE_NS = re.compile(r'^urn:lti:(?:inst|sys)?role:ims/lis/([A-Za-z]+)$')

    def authorize(self, blti, role='member'):
        if blti is None:
            raise BLTIException('Missing LTI parameters')

        lti_consumer = blti.data.get(
            'tool_consumer_info_product_family_code', '').lower()

        if lti_consumer == 'canvas':
            if (not role or role == 'public'):
                pass
            elif (role in self.CANVAS_ROLES):  # member/admin
                self._has_role(blti, self.CANVAS_ROLES[role])
            else:  # specific role?
                self._has_role(blti, [role])
        else:
            raise BLTIException('authorize() not implemented for "%s"!' % (
                lti_consumer))

    def _has_role(self, blti, valid_roles):
        roles = blti.data.get('roles', '').split(',')
        for role in roles:
            if role in valid_roles:
                return

            m = self.RE_ROLE_NS.match(role)
            if m and m.group(1) in valid_roles:
                return

        raise BLTIException('You are not authorized to view this content')
