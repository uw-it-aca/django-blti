# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from .base import BLTIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from blti.config import get_tool_conf, get_launch_data_storage
from blti.request import BLTIRequest
from blti.exceptions import BLTIException
from blti.validators import BLTIRequestValidator
from blti.launch_redirect import BLTILaunchRedirect
from blti.cookie import BLTICookieService
from pylti1p3.exception import OIDCException
from pylti1p3.contrib.django import DjangoMessageLaunch
from oauthlib.oauth1.rfc5849.endpoints.signature_only import (
    SignatureOnlyEndpoint)
from pylti1p3.contrib.django.session import DjangoSessionService
from urllib.parse import urljoin, urlparse, urlencode
import json
import logging


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class BLTILaunchView(BLTIView):
    http_method_names = ['get', 'post']
    _oidc_launch_keys = ['state', 'authenticity_token', 'id_token', 'utf8']
    _oidc_launch_client_store_state = 'lti1p3_state'
    _oidc_launch_client_store_session_id = 'lti1p3_session_id'
    _oidc_launch_client_store_nonce = 'lti1p3_nonce'

    def post(self, request, *args, **kwargs):
        return self._launch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self._launch(request, *args, **kwargs)

    def _launch(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def dispatch(self, request, *args, **kwargs):
        try:
            launch_data = self.validate_1p1(request)
            logger.debug(f"LTI 1.1 launch")
        except BLTIException as ex:
            try:
                if self._missing_lti_parameters(request):
                    return self._client_store_redirect(request)

                launch_data = self.validate_1p3(request)
                logger.debug(f"LTI 1.3 launch")
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

        self.set_session(**launch_data)
        return super(BLTILaunchView, self).dispatch(request, *args, **kwargs)

    def validate_1p1(self, request):
        request_validator = BLTIRequestValidator()
        endpoint = SignatureOnlyEndpoint(request_validator)
        uri = request.build_absolute_uri()
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        valid, oauth_req = endpoint.validate_request(
            uri, request.method, request.body, headers)

        # if non-ssl fixup scheme to validate signature generated
        # on the other side of ingress
        if not valid and uri.startswith('http:') and request.is_secure():
            valid, oauth_req = endpoint.validate_request(
                f"https{uri[4:]}", request.method, request.body, headers)

        if not valid:
            raise BLTIException('Invalid OAuth Request')

        blti_params = dict(oauth_req.params)
        return blti_params

    def validate_1p3(self, request):
        tool_conf = get_tool_conf()
        launch_data_storage = get_launch_data_storage()
        message_launch = DjangoMessageLaunch(
            request, tool_conf, launch_data_storage=launch_data_storage)
        return message_launch.get_launch_data()

    def _missing_lti_parameters(self, request):
        blti_request = BLTIRequest(request)
        cookie_service = BLTICookieService(blti_request)
        session_service = DjangoSessionService(request)
        data_storage = get_launch_data_storage()
        data_storage.set_request(blti_request)

        session_cookie_name = data_storage.get_session_cookie_name()
        session_id = cookie_service.get_cookie(session_cookie_name)
        if not session_id:
            # peel parameters inserted from client side storage
            # off and insert them into the request validation
            session_id = self.get_parameter(
                request, self._oidc_launch_client_store_session_id)
            if session_id:
                # insert request session cookie
                cookie_service.set_request_cookie(
                    session_cookie_name, session_id)

                # insert request state cookie
                state = self.get_parameter(
                    request, self._oidc_launch_client_store_state)
                cookie_service.set_request_cookie(state, state)

                # add nonce to session
                nonce = self.get_parameter(
                    request, self._oidc_launch_client_store_nonce)
                session_service.save_nonce(nonce)

                # fall thru to 1.3 launch

            elif self.get_parameter(request, 'lti_storage_target'):
                return True

        return False

    def _client_store_redirect(self, request):
        redirect_uri = request.build_absolute_uri()

        if redirect_uri.startswith('http:') and request.is_secure():
            redirect_uri = f"https{uri[4:]}"

        parameters = {k: self.get_parameter(request, k) for (
            k) in self._oidc_launch_keys}
        auth_origin = self._login_origin_from_iss(parameters['id_token'])

        logger.debug(f"LTI 1.3 client side storage redirect")
        return BLTILaunchRedirect(
            redirect_uri, parameters, auth_origin).do_js_redirect()

    def _login_origin_from_iss(self, id_token):
        # oidc auth origin from iss dug out of jwt
        jwt = self._jwt_from_id_token(id_token)
        iss = jwt.get('iss')
        reg = get_tool_conf().find_registration_by_issuer(iss)
        auth_url = urlparse(reg.get_auth_token_url())
        return f"{auth_url.scheme}://{auth_url.netloc}"

    def _jwt_from_id_token(self, id_token):
        parts = id_token.split('.')
        if len(parts) != 3:
            raise BLTIException("Invalid id_token")

        raw_body = DjangoMessageLaunch.urlsafe_b64decode(parts[1])
        return json.loads(raw_body)

    def get_parameter(self, request, key):
        params = request.POST if request.method == 'POST' else request.GET
        return params.get(key)
