# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.db import models


LTI_DATA_CLAIM_BASE =  'https://purl.imsglobal.org/spec/lti/claim/'


class LTILaunchData(object):
    def __init__(self, **data):
        self._data = data
        self.platform_name = data.get(
            'tool_consumer_info_product_family_code',
            self.claim_tool_platform('product_family_code'))

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
