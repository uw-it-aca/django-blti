# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.db import models
from pylti1p3.roles import (
    AbstractRole, StaffRole, TeachingAssistantRole,
    DesignerRole, ObserverRole, TransientRole)
import re


LTI_DATA_CLAIM_BASE = 'https://purl.imsglobal.org/spec/lti/claim/'


# Instructor and student roles are specific to the given context (course)
class TeacherRole(AbstractRole):
    _common_roles = ("Instructor", "Administrator")
    _context_roles = ("Instructor", "Administrator")


class StudentRole(AbstractRole):
    _common_roles = ("Learner")
    _context_roles = ("Learner")


class LTILaunchData(object):
    def __init__(self, **data):
        self._data = data
        self.platform_name = self._data.get(
            'tool_consumer_info_product_family_code',
            self.claim_tool_platform('product_family_code'))

        self.is_member = self._1p1_roles(
            ['member']) or (
                StaffRole(self._data).check() or
                TeacherRole(self._data).check() or
                TeachingAssistantRole(self._data).check() or
                StudentRole(self._data).check() or
                ObserverRole(self._data).check())

        self.is_administrator = self._1p1_roles(
            ['admin']) or (
                TeacherRole(self._data).check() or
                TeachingAssistantRole(self._data).check() or
                DesignerRole(self._data).check())

        self.is_staff = self._1p1_roles(
            ['Administrator']) or (
                StaffRole(self._data).check())

        self.is_instructor = self._1p1_roles(
            ['Instructor']) or (
                TeacherRole(self._data).check())

        self.is_teaching_assistant = self._1p1_roles(
            ['TeachingAssistant']) or (
                TeachingAssistantRole(self._data).check())

        self.is_student = self._1p1_roles(
            ['Learner']) or (
                StudentRole(self._data).check())

        self.is_designer = self._1p1_roles(
            ['ContentDeveloper']) or (
                DesignerRole(self._data).check())

    def _1p1_roles(self, valid_roles):
        RE_ROLE_NS = re.compile(
            r'^urn:lti:(?:inst|sys)?role:ims/lis/([A-Za-z]+)$')
        AGGREGATE_ROLES = {
            'member': ['Administrator', 'Instructor', 'TeachingAssistant',
                       'ContentDeveloper', 'Learner', 'Observer'],
            'admin': ['Administrator', 'Instructor', 'TeachingAssistant',
                      'ContentDeveloper'],
        }

        try:
            roles = self._data['roles'].split(',')
        except KeyError:
            return False

        for valid_role in valid_roles:
            if valid_role in AGGREGATE_ROLES:
                return self._1p1_roles(AGGREGATE_ROLES[valid_role])

            for role in roles:
                if role == valid_role:
                    return True

                m = RE_ROLE_NS.match(role)
                if m and m.group(1) and m.group(1) == valid_role:
                    return True

        return False

    def claim_tool_platform(self, key, default=None):
        return self._claim_data('tool_platform', key, default)

    def claim_lis(self, key, default=None):
        return self._claim_data('lis', key, default)

    def claim_context(self, key, default=None):
        return self._claim_data('context', key, default)

    def claim_resource_link(self, key, default=None):
        return self._claim_data('resource_link', key, default)

    def claim_launch_presentation(self, key, default=None):
        return self._claim_data('launch_presentation', key, default)

    def claim_custom(self, key, default=None):
        return self._claim_data('custom', key, default)

    def _claim_data(self, claim, key, default=None):
        # sniff at the 1.3 claim, then sniff at corresponding 1.1 key
        return self._data.get(self._claim(claim), {}).get(
            key, self._data.get(f"{claim}_{key}", default))

    def _claim(self, claim):
        # specific claim key
        return f"{LTI_DATA_CLAIM_BASE}{claim}"
