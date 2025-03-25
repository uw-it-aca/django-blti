# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from pylti1p3.contrib.django.request import DjangoRequest
import logging


logger = logging.getLogger(__name__)


class BLTIRequest(DjangoRequest):
    def __init__(self, request, post_only=False, default_params=None):
        super().__init__(request, post_only, default_params)

    def get_origin(self):
        for key, value in self._request.META.items():
            logger.debug(f"META[{key}]: {value}")
        return self._request.META.get('HTTP_ORIGIN')
