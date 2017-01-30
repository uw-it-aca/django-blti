from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from blti import BLTI, BLTIException
from blti.validators import BLTIOauth, BLTIRoles
try:
    from urllib import unquote_plus
except ImportError:
    from urllib.parse import unquote_plus  # Python3


class BLTIView(TemplateView):
    http_method_names = ['get', 'options']

    def get(self, request, *args, **kwargs):
        try:
            params = self.validate(request)
        except BLTIException as err:
            self.template_name = 'blti/401.html'
            return self.render_to_response({})

        context = self.get_context_data(
            request=request, blti_params=params, **kwargs)

        response = self.render_to_response(context)
        self.add_headers(response=response, blti_params=params, **kwargs)
        return response

    def get_context_data(self, **kwargs):
        return kwargs

    def add_headers(self, **kwargs):
        pass

    def get_session(self, request):
        return BLTI().get_session(request)

    def set_session(self, request, **kwargs):
        BLTI().set_session(request, **kwargs)

    def validate(self, request):
        return self.get_session(request)


class BLTILaunchView(BLTIView):
    http_method_names = ['post']
    authorized_role = 'member'

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(BLTILaunchView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            params = self.validate(request)
            self.set_session(request, **params)
        except BLTIException as err:
            self.template_name = 'blti/error.html'
            return self.render_to_response({'error': err})

        context = self.get_context_data(
            request=request, blti_params=params, **kwargs)

        response = self.render_to_response(context)
        self.add_headers(response=response, blti_params=params, **kwargs)
        return response

    def validate(self, request):
        params = {}
        body = request.read()
        if body and len(body):
            params = dict((k, v) for k, v in [tuple(
                map(unquote_plus, kv.split('='))
            ) for kv in body.split('&')])
        else:
            raise BLTIException('Missing or malformed parameter or value')

        blti_params = BLTIOauth().validate(request, params=params)
        if blti_params:
            BLTIRoles().validate(blti_params, visibility=self.authorized_role)

        return blti_params


class RawBLTIView(BLTILaunchView):
    template_name = 'blti/raw.html'
    authorized_role = 'admin'
