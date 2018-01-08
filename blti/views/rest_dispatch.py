from django.conf import settings
from django.views import View
from django.http import HttpResponse
from blti import BLTI, BLTIException
from blti.models import BLTIData
from blti.validators import BLTIRoles
from blti.performance import log_response_time
import json
import re


class RESTDispatch(View):
    """
    A superclass for API views
    """
    authorized_role = 'member'
    extra_response_headers = {}

    @log_response_time
    def dispatch(self, request, *args, **kwargs):
        try:
            kwargs['blti_params'] = self.validate(request)
        except BLTIException as ex:
            return self.error_response(401, ex)

        return super(RESTDispatch, self).dispatch(request, *args, **kwargs)

    # Backwards-compatible method
    def run(self, request, *args, **kwargs):
        return self.dispatch(request, *args, **kwargs)

    def validate(self, request):
        blti_params = self.get_session(request)
        self.authorize(blti_params)
        return blti_params

    def authorize(self, blti_params):
        BLTIRoles().validate(blti_params, visibility=self.authorized_role)
        self.blti = BLTIData(blti_params)

    def get_session(self, request):
        return BLTI().get_session(request)

    def error_response(self, status, message='', content={}):
        content['error'] = str(message)
        return self.json_response(content=content, status=status)

    def json_response(self, content={}, status=200):
        return self._http_response(json.dumps(content),
                                   status=status,
                                   content_type='application/json')

    def _http_response(self, content, *args, **kwargs):
        response = HttpResponse(content, *args, **kwargs)
        for k, v in self.extra_response_headers.iteritems():
            response[k] = v

        return response
