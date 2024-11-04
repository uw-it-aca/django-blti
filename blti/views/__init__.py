# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import os
import json
import logging
from importlib import resources
from django.http import HttpResponse
from django.conf import settings
from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from pylti1p3.exception import LtiException
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.contrib.django import (
    DjangoOIDCLogin, DjangoMessageLaunch, DjangoCacheDataStorage)
from blti.models import BLTIData
from blti.exceptions import BLTIException
from blti.validators import BLTIRequestValidator, Roles
from blti.performance import log_response_time
from oauthlib.oauth1.rfc5849.endpoints.signature_only import (
    SignatureOnlyEndpoint)


logger = logging.getLogger(__name__)
LTI1P3_CONFIG_DIRECTORY_NAME = 'lti_config'
LTI1P3_CONFIG_FILE_NAME = 'tool.json'


def get_mock_config_directory():
    os.path.join(resources.files('blti'), 'resources', 'lti_config')


def get_lti_config_directory():
    directory = os.environ.get(
        'LTI_CONFIG_DIRECTORY',
        os.path.join(settings.BASE_DIR, '..', LTI1P3_CONFIG_DIRECTORY_NAME))
    return get_mock_config_directory() if directory == 'MOCK' else directory


def get_lti_config_path():
    return os.path.join(get_lti_config_directory(), LTI1P3_CONFIG_FILE_NAME)


def get_tool_conf():
    return ToolConfJsonFile(get_lti_config_path())


def get_jwk_from_public_key(key_name):
    key_path = os.path.join(get_lti_config_directory(), key_name)
    with open(key_path, 'r') as f:
        return Registration.get_jwk(f.read())


def get_launch_data_storage():
    return DjangoCacheDataStorage()


def get_launch_url(request):
    try:
        return request.POST.get(
            'target_link_uri', request.GET['target_link_uri'])
    except KeyError:
        raise Exception('Missing "target_link_uri" param')


def login(request):
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()

    oidc_login = DjangoOIDCLogin(
        request, tool_conf, launch_data_storage=launch_data_storage)
    target_link_uri = get_launch_url(request)
    logger.info('login redirect: %s', target_link_uri)
    return oidc_login.enable_check_cookies().redirect(target_link_uri)


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

    def set_session(self, request, **kwargs):
        BLTI().set_session(request, **kwargs)

    def get_session(self, request):
        return BLTI().get_session(request)

    def validate(self, request):
        if request.method != 'OPTIONS':
            self.authorize(request, self.authorized_role)

    def authorize(self, role):
        Roles().authorize(self.get_session(request), role=role)


@method_decorator(csrf_exempt, name='dispatch')
class BLTILaunchView(BLTIView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def validate(self, request):
        try:
            return self.validate_1p1(request)
        except BLTIException as ex:
            try:
                return self.validate_1p3(request)
            except LtiException as exx:
                logger.error(f"LTI launch error: {ex}")
                self.template_name = 'blti/401.html'
                return self.render_to_response({'error': str(ex)}, status=401)

        super(BLTILaunchView, self).validate(request)

    def validate_1p3(self, request):
        tool_conf = get_tool_conf()
        launch_data_storage = get_launch_data_storage()

        message_launch = DjangoMessageLaunch(
            request, tool_conf, launch_data_storage=launch_data_storage)
        message_launch_data = message_launch.get_launch_data()
        self.set_session(request, **message_launch_data)

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
        self.set_session(request, **blti_params)


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
