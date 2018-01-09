from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from blti import BLTI, BLTIException
from blti.models import BLTIData
from blti.validators import BLTIOauth, BLTIRoles
from blti.performance import log_response_time
import json
try:
    from urllib import unquote_plus
except ImportError:
    from urllib.parse import unquote_plus  # Python3


class BLTIView(TemplateView):
    authorized_role = 'member'

    def dispatch(self, request, *args, **kwargs):
        try:
            kwargs['blti_params'] = self.validate(request)
        except BLTIException as err:
            self.template_name = 'blti/401.html'
            return self.render_to_response({'error': err}, status=401)

        return super(BLTIView, self).dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **kwargs):
        response = super(BLTIView, self).render_to_response(context, **kwargs)
        self.add_headers(response=response, **kwargs)
        return response

    def add_headers(self, **kwargs):
        pass

    def get_session(self, request):
        return BLTI().get_session(request)

    def set_session(self, request, **kwargs):
        BLTI().set_session(request, **kwargs)

    def validate(self, request):
        blti_params = self.get_session(request)
        self.authorize(blti_params)
        return blti_params

    def authorize(self, blti_params):
        BLTIRoles().validate(blti_params, visibility=self.authorized_role)
        self.blti = BLTIData(**blti_params)


class BLTILaunchView(BLTIView):
    http_method_names = ['post']

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(BLTILaunchView, self).dispatch(request, *args, **kwargs)

    def validate(self, request):
        params = {}
        body = request.read()
        try:
            params = dict((k, v) for k, v in [tuple(
                map(unquote_plus, kv.split('='))
            ) for kv in body.split('&')])
        except Exception:
            raise BLTIException('Missing or malformed parameter or value')

        blti_params = BLTIOauth().validate(request, params=params)
        self.authorize(blti_params)
        self.set_session(request, **blti_params)

        return blti_params

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class RawBLTIView(BLTILaunchView):
    template_name = 'blti/raw.html'
    authorized_role = 'admin'


class RESTDispatch(BLTIView):
    """
    A superclass for API views
    """
    authorized_role = 'member'

    @log_response_time
    def dispatch(self, request, *args, **kwargs):
        try:
            kwargs['blti_params'] = self.validate(request)
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
        self.add_headers(response=response, **kwargs)
        return response
