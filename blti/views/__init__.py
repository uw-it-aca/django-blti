# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import json
import logging
from django.http import HttpResponse
from django.conf import settings
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from blti.models import BLTIData
from blti.validators import Roles
from blti.performance import log_response_time
from blti.exceptions import BLTIException
from pylti1p3.exception import LtiException
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.contrib.django import (
    DjangoOIDCLogin, DjangoMessageLaunch, DjangoCacheDataStorage)


logger = logging.getLogger(__name__)
CONFIG_DIRECTORY_NAME = 'lti_config'
CONFIG_FILE_NAME = 'tool.json'


def get_lti_config_directory():
    return os.environ.get(
        'LTI_CONFIG_DIRECTORY',
        os.path.join(settings.BASE_DIR, '..', CONFIG_DIRECTORY_NAME))


def get_lti_config_path():
    return os.path.join(get_lti_config_directory(), CONFIG_FILE_NAME)


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


class BLTIViewBase(TemplateView):
    authorized_role = 'member'

    def render_to_response(self, context, **kwargs):
        response = super(
            BLTIViewBase, self).render_to_response(context, **kwargs)
        self.add_headers(response=response, **kwargs)
        return response

    def validate_session_and_role(self, request):
        try:
            if request.method != 'OPTIONS':
                launch_data = request.session.get('lti_launch_data', {})
                self.blti = BLTIData(**launch_data)
                self.authorize_role(self.authorized_role)
        except BLTIException as err:
            self.template_name = 'blti/401.html'
            return self.render_to_response({'error': str(err)}, status=401)

    def authorize_role(self, role):
        Roles().authorize(self.blti, role=role)


@method_decorator(csrf_exempt, name='dispatch')
class BLTILaunchView(BLTIViewBase):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        tool_conf = get_tool_conf()
        launch_data_storage = get_launch_data_storage()

        try:
            message_launch = DjangoMessageLaunch(
                request, tool_conf, launch_data_storage=launch_data_storage)
            message_launch_data = message_launch.get_launch_data()
            request.session['lti_launch_data'] = message_launch_data
        except LtiException as err:
            logger.error(f"LTI launch error: {err}")
            self.template_name = 'blti/401.html'
            return self.render_to_response({'error': str(err)}, status=401)

        self.validate_session_and_role(request)

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class BLTIView(BLTIViewBase):
    def dispatch(self, request, *args, **kwargs):
        self.validate_session_and_role(request)
        return super(BLTIView, self).dispatch(request, *args, **kwargs)

    def add_headers(self, **kwargs):
        pass


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
