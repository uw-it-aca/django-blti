# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from pylti1p3.exception import LtiException, OIDCException
from pylti1p3.contrib.django import DjangoOIDCLogin, DjangoMessageLaunch
from blti import BLTI
from blti.models import BLTIData
from blti.config import get_tool_conf, get_launch_data_storage
from blti.exceptions import BLTIException
from blti.validators import BLTIRequestValidator, Roles
from blti.performance import log_response_time
from oauthlib.oauth1.rfc5849.endpoints.signature_only import (
    SignatureOnlyEndpoint)


logger = logging.getLogger(__name__)


def get_jwk_from_public_key(key_name):
    with open(get_lti_public_key_path(key_name), 'r') as f:
        return Registration.get_jwk(f.read())


def get_launch_url(request):
    try:
        return request.POST.get(
            'target_link_uri', request.GET.get('target_link_uri'))
    except KeyError:
        raise BLTIException('Missing "target_link_uri" param')


def login(request):
    try:
        tool_conf = get_tool_conf()
        launch_data_storage = get_launch_data_storage()

        oidc_login = DjangoOIDCLogin(
            request, tool_conf, launch_data_storage=launch_data_storage)
        target_link_uri = get_launch_url(request)
        return oidc_login.enable_check_cookies().redirect(target_link_uri)
    except Exception as ex:
        return HttpResponse(str(ex), status=401)


def get_jwks(request):
    tool_conf = get_tool_conf()
    return JsonResponse(tool_conf.get_jwks(), safe=False)


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
        # legacy reference to LTI launch data
        self.blti = BLTIData(**self.get_session())

        if request.method != 'OPTIONS':
            self.authorize(self.authorized_role)

    def authorize(self, role):
        Roles().authorize(self.blti, role=role)


@method_decorator(csrf_exempt, name='dispatch')
class BLTILaunchView(BLTIView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def dispatch(self, request, *args, **kwargs):
        try:
            self.validate_1p1(request)
        except BLTIException as ex:
            try:
                self.validate_1p3(request)
            except OIDCException as ex:
                logger.error(f"LTI authentication failure: {ex}")
                self.template_name = 'blti/401.html'
                return self.render_to_response(
                    {'LTI authentication failure': str(ex)}, status=401)
            except Exception as ex:
                logger.error(f"LTI launch error: {ex}")
                self.template_name = 'blti/401.html'
                return self.render_to_response(
                    {'LTI launch failure': str(ex)}, status=401)

        return super(BLTILaunchView, self).dispatch(request, *args, **kwargs)

    def validate_1p3(self, request):
        tool_conf = get_tool_conf()
        launch_data_storage = get_launch_data_storage()

        message_launch = DjangoMessageLaunch(
            request, tool_conf, launch_data_storage=launch_data_storage)
        message_launch_data = message_launch.get_launch_data()
        self.set_session(**message_launch_data)

    def validate_1p1(self, request):
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
        self.set_session(**blti_params)


class RawBLTIView(BLTILaunchView):
    template_name = 'blti/raw.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        return {'blti_params': sorted(self.get_session().items())}


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
