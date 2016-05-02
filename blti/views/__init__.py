from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from blti import BLTI, BLTIException
from blti.validators import BLTIOauth, BLTIRoles
from urllib import unquote_plus


class BLTIView(TemplateView):
    http_method_names = ['get', 'options']

    def get(self, request, *args, **kwargs):
        try:
            params = self.validate(request)
        except BLTIException as err:
            return self.error_view('blti/401.html')

        context = self.get_context_data(
            request=request, blti_params=params, **kwargs)

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        return kwargs

    def get_session(request):
        return BLTI().get_session(request)

    def set_session(request, params):
        BLTI().set_session(request, **params)

    def validate(self, request):
        return self.get_session(request)

    def error_view(self, template_name, **kwargs):
        self.template_name = template_name
        return self.render_to_response(**kwargs)


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
            return self.error_view('blti/error.html', error=err)

        context = self.get_context_data(
            request=request, blti_params=params, **kwargs)
        return self.render_to_response(context)

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
