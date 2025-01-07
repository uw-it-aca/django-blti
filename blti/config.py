# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import os
from django.conf import settings
from importlib import resources
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.contrib.django import DjangoCacheDataStorage


LTI1P3_CONFIG_DIRECTORY_NAME = 'lti_config'
LTI1P3_CONFIG_FILE_NAME = 'tool.json'


def get_tool_conf():
    return ToolConfJsonFile(get_lti_config_path())


def get_launch_data_storage():
    return DjangoCacheDataStorage()


def get_lti_config_directory():
    return os.environ.get(
        'LTI_CONFIG_DIRECTORY',
        os.path.join(settings.BASE_DIR, LTI1P3_CONFIG_DIRECTORY_NAME))


def get_lti_config_path():
    return os.path.join(get_lti_config_directory(), LTI1P3_CONFIG_FILE_NAME)


def get_lti_public_key_path(key_name):
    return os.path.join(get_lti_config_directory(), key_name)
