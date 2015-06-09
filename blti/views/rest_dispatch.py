from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from blti import BLTI, BLTIException
import json
import re


class RESTDispatch(object):
    """ A superclass for views, that handles passing on the request to the
        appropriate view method, based on the request method.
    """
    @never_cache
    def run(self, *args, **named_args):
        request = args[0]

        try:
            BLTI().get_session(request)
        except BLTIException as ex:
            if (not getattr(settings, 'BLTI_NO_AUTH', False) and
                    not request.user.is_authenticated()):
                return self.error_response(401, "%s" % ex)

        return self.run_http_method(*args, **named_args)

    def run_http_method(self, *args, **named_args):
        request = args[0]

        if (re.match(r'(GET|HEAD|POST|PUT|DELETE|PATCH)', request.method) and
                hasattr(self, request.method)):
            return getattr(self, request.method)(*args, **named_args)
        else:
            return self.invalid_method(*args, **named_args)

    def invalid_method(self, *args, **named_args):
        return HttpResponse('Method not allowed', status=405)

    def error_response(self, status, message='', content={}):
        content['error'] = message
        return HttpResponse(json.dumps(content),
                            status=status,
                            content_type='application/json')

    def json_response(self, content='', status=200):
        return HttpResponse(json.dumps(content),
                            status=status,
                            content_type='application/json')
