# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


LTI_1p3_ROLES_CLAIM = "https://purl.imsglobal.org/spec/lti/claim/roles"
LTI_1p3_ROLE_PREFIX = "http://purl.imsglobal.org/vocab/lis/v2/"


def roles_from_role_name(role_names):
    roles = []

    for role_name in role_names:
        if role_name == 'User':
            roles += ["system/person#User"]
        elif role_name in ['Observer', 'Mentor']:
            roles += [
                "institution/person#Observer",
                "institution/person#Mentor",
                "membership#Mentor"]
        elif role_name in ['Student', 'Learner']:
            roles += [
                "institution/person#Learner",
                "institution/person#Student",
                "membership#Learner"]
        elif role_name in ['Instructor', 'Faculty', 'Teacher']:
            roles += [
                "institution/person#Instructor",
                "institution/person#Faculty",
                "membership#Instructor"]
        elif role_name == 'Administrator':
            roles += [
                "system/person#User",
                "institution/person#Administrator",
                "membership#Administrator"]
        elif role_name == 'TeachingAssistant':
            roles += ["membership/Instructor#TeachingAssistant"]
        elif role_name == 'ContentDeveloper':
            roles += ["membership#ContentDeveloper"]

    return LTI_1p3_ROLES_CLAIM, [f"{LTI_1p3_ROLE_PREFIX}{r}" for r in roles]
