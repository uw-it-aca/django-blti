# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from blti.exceptions import BLTIException
import json


LTI_DATA_KEY = 'lti_launch_data'


class BLTI(object):
    def set_session(self, request, **kwargs):
        if not request.session.exists(request.session.session_key):
            request.session.create()

        # filter oauth_* parameters
        for key in list(filter(
                lambda key: key.startswith('oauth_'), kwargs.keys())):
            kwargs.pop(key)

        request.session[LTI_DATA_KEY] = json.dumps(kwargs)

    def get_session(self, request):
        try:
            return json.loads(request.session[LTI_DATA_KEY])
        except KeyError:
            raise BLTIException('Invalid Session')
