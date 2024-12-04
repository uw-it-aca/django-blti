# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from blti import BLTI
from blti.models import CanvasData
from blti.exceptions import BLTIException
from blti.validators import Roles


@method_decorator(csrf_exempt, name='dispatch')
class BLTIView(TemplateView):
    authorized_role = 'member'

    def dispatch(self, request, *args, **kwargs):
        try:
            self.validate(request)
        except BLTIException as err:
            self.template_name = 'blti/401.html'
            return self.render_to_response({'error': str(err)}, status=401)

        return super(BLTIView, self).dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **kwargs):
        response = super(BLTIView, self).render_to_response(context, **kwargs)
        self.add_headers(response=response, **kwargs)
        return response

    def add_headers(self, **kwargs):
        pass

    def set_session(self, **kwargs):
        BLTI().set_session(self.request, **kwargs)

    def get_session(self):
        return BLTI().get_session(self.request)

    def validate(self, request):
        self.blti = self.launch_data_model()

        if request.method != 'OPTIONS':
            self.authorize(self.authorized_role)

    def authorize(self, role):
        Roles(self.blti).authorize(role=role)

    def launch_data_model(self):
        return CanvasData(**self.get_session())
