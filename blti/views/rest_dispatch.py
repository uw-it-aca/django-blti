from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from blti import BLTI, BLTIException
from blti.performance import log_response_time
import json
import re


class RESTDispatchAuthorization(Exception):
    pass


class RESTDispatchMethod(Exception):
    pass


class RESTDispatch(object):
    """ A superclass for views, that handles passing on the request to the
        appropriate view method, based on the request method.
    """

    extra_response_headers = {}

    @never_cache
    @log_response_time
    def run(self, *args, **named_args):
        try:
            request = args[0]
            self.authorize(request)
            return self.dispatch(request.method)(*args, **named_args)
        except RESTDispatchAuthorization as ex:
            return self.error_response(401, ex)
        except RESTDispatchMethod:
            return self.error_response(405, 'Method not allowed')

    def _http_response(self, content, *args, **kwargs):
        response = HttpResponse(content, *args, **kwargs)
        for k, v in self.extra_response_headers.iteritems():
            response[k] = v

        return response

    def get_session(self, request):
        return BLTI().get_session(request)

    def authorize(self, request):
        self.blti_authorize(request)

    def blti_authorize(self, request):
        try:
            self.get_session(request)
        except BLTIException as ex:
            if not (getattr(settings, 'BLTI_NO_AUTH', False) and
                    request.user.is_authenticated()):
                raise RESTDispatchAuthorization('%s' % ex)

    def dispatch(self, method):
        methods = dict((m, m) for m in ['GET', 'HEAD', 'POST', 'PUT',
                                        'DELETE', 'PATCH', 'OPTIONS'])
        try:
            return getattr(self, methods[method])
        except (KeyError, AttributeError):
            raise RESTDispatchMethod()

    def error_response(self, status, message='', content={}):
        content['error'] = str(message)
        return self.json_response(content=content, status=status)

    def json_response(self, content={}, status=200):
        return self._http_response(json.dumps(content),
                                   status=status,
                                   content_type='application/json')
