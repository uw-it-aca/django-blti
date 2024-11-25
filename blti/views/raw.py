# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import json
from .launch import BLTILaunchView


class BLTIRawView(BLTILaunchView):
    template_name = 'blti/raw.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        return {
            'digested_lti_params': [(k, getattr(
                self.blti, k)) for k in sorted(vars(self.blti)) if (
                    not k.startswith("_"))],
            'raw_lti_params': json.dumps(self.get_session(), indent=4)
        }
