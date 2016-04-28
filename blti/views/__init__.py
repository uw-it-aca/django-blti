from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from blti import BLTI, BLTIException
from blti.validators import BLTIOauth, BLTIRoles
from urllib import unquote_plus


class BLTILaunchView(TemplateView):
    http_method_names = ['post']
    authorized_role = 'member'

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(BLTILaunchView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            params = self.validate(request)
            BLTI().set_session(request, **params)

        except BLTIException as err:
            params = {'validation_error': err}
            self.template_name = 'blti/error.html'

        context = self.get_context_data(request=request, blti_params=params,
                                        **kwargs)
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

    def get_context_data(self, **kwargs):
        return kwargs


class RawBLTIView(BLTILaunchView):
    template_name = 'blti/raw.html'
    authorized_role = 'admin'
