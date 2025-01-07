# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from importlib import resources
import json
import os
import logging


MOCK_JWT_FILE = ('resources', 'lti1p3', 'file', 'jwt.json')
logger = logging.getLogger(__name__)


class Mock1p3Data:
    def launch_data(self):
        mock_jwt_file = os.path.join(*MOCK_JWT_FILE)
        mock_jwt_path = os.path.join(
            resources.files('blti'), mock_jwt_file)

        for app in settings.INSTALLED_APPS:
            try:
                path = os.path.join(resources.files(app), mock_jwt_file)
            except Exception:
                continue

            logger.debug(f"Checking for mock jwt: {path}")
            if path != mock_jwt_path and os.path.exists(path):
                mock_jwt_path = path
                break

        logger.debug(f"Using mock jwt: {mock_jwt_path}")
        with open(mock_jwt_path, 'r') as f:
            return json.load(f)
