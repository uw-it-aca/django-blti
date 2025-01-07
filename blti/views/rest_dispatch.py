# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.http import HttpResponse
from .base import BLTIView
from blti.exceptions import BLTIException
from blti.performance import log_response_time
import json


class RESTDispatch(BLTIView):
    """
    A superclass for API views
    """
    authorized_role = 'member'

    @log_response_time
    def dispatch(self, request, *args, **kwargs):
        try:
            self.validate(request)
        except BLTIException as ex:
            return self.error_response(401, ex)

        return super(BLTIView, self).dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **kwargs):
        return self.json_response(content=context)

    def error_response(self, status, message='', content={}):
        content['error'] = str(message)
        return self.json_response(content=content, status=status)

    def json_response(self, content={}, status=200):
        response = HttpResponse(json.dumps(content),
                                status=status,
                                content_type='application/json')
        self.add_headers(response=response)
        return response
