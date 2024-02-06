# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import json
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from blti import BLTI, BLTIException
from blti.models import BLTIData
from blti.validators import BLTIRequestValidator, Roles
from blti.performance import log_response_time
from oauthlib.oauth1.rfc5849.endpoints.signature_only import (
    SignatureOnlyEndpoint)


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

    def get_session(self, request):
        return BLTI().get_session(request)

    def set_session(self, request, **kwargs):
        BLTI().set_session(request, **kwargs)

    def validate(self, request):
        if request.method != 'OPTIONS':
            blti_params = self.get_session(request)
            self.blti = BLTIData(**blti_params)
            self.authorize(self.authorized_role)

    def authorize(self, role):
        Roles().authorize(self.blti, role=role)


class BLTILaunchView(BLTIView):
    http_method_names = ['post']

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(BLTILaunchView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def validate(self, request):
        request_validator = BLTIRequestValidator()
        endpoint = SignatureOnlyEndpoint(request_validator)
        uri = request.build_absolute_uri()
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        body = request.read()

        valid, oauth_req = endpoint.validate_request(
            uri, request.method, body, headers)

        # if non-ssl fixup scheme to validate signature generated
        # on the other side of ingress
        if (not valid and
                request_validator.enforce_ssl is False and
                uri[:5] == "http:"):
            valid, oauth_req = endpoint.validate_request(
                "https{}".format(uri[4:]), request.method, body, headers)

        if not valid:
            raise BLTIException('Invalid OAuth Request')

        blti_params = dict(oauth_req.params)
        self.set_session(request, **blti_params)

        super(BLTILaunchView, self).validate(request)


class RawBLTIView(BLTILaunchView):
    template_name = 'blti/raw.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        return {'blti_params': sorted(self.blti.data.items())}


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
