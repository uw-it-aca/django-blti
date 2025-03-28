# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from .base import BLTIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from blti.config import get_tool_conf, get_launch_data_storage
from blti.exceptions import BLTIException
from blti.validators import BLTIRequestValidator
from blti.launch_redirect import BLTILaunchRedirect
from pylti1p3.exception import OIDCException
from pylti1p3.contrib.django import DjangoMessageLaunch
from oauthlib.oauth1.rfc5849.endpoints.signature_only import (
    SignatureOnlyEndpoint)
from pylti1p3.contrib.django.request import DjangoRequest
from pylti1p3.contrib.django.cookie import DjangoCookieService
from pylti1p3.contrib.django.session import DjangoSessionService
from urllib.parse import urljoin, urlparse, urlencode
import json
import logging


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class BLTILaunchView(BLTIView):
    http_method_names = ['get', 'post']

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
                # if client storage indicated, redirect to collect cookies
                django_request = DjangoRequest(request)
                cookie_serice = DjangoCookieService(django_request)
                session_service = DjangoSessionService(request)
                data_storage = get_launch_data_storage()
                data_storage.set_request(django_request)

                session_cookie_name = data_storage._prepare_key(
                    data_storage.get_session_cookie_name())

                logger.debug("session id: lti1p3_session_id_name: "
                             f"{session_cookie_name}")

                session_id = cookie_serice.get_cookie(session_cookie_name)

                logger.debug(f"session cookie: {session_cookie_name} = "
                             f"{session_id}")

                if not session_id:
                    # peel params inserted from client side storage
                    # off and insert them into the request validation
                    session_id = self.get_parameter(
                        request, 'session_id')

                    logger.debug(f"parameter: lti1p3_session_cookie = "
                                 f"{session_id}")

                    if session_id:
                        logger.debug(f"BOUNCED: LTI client store params found")

                        # insert session cookie
                        cookie_serice.set_cookie(
                            data_storage.get_session_cookie_name(),
                            session_id)
                        logger.debug(
                            "BOUNCED: set cookie: "
                            f"{data_storage.get_session_cookie_name()} = "
                            f"{session_id}")

                        # insert state cookie
                        cookie_serice.set_cookie(f"lti1p3-{state}", state)
                        logger.debug(
                            f"BOUNCED: set cookie: lti1p3-{state}: {state}")
                        state = self.get_parameter(request, 'lti1p3_state')

                        # add nonce to session
                        nonce = self.get_parameter(request, 'lti1p3_nonce')
                        session_service.save_nonce(nonce)
                        logger.debug(f"BOUNCED: saved session nonce: {nonce}")

                        logger.debug(f"BOUNCED: falling thru to validate")

                    elif self.get_parameter(request, 'lti_storage_target'):
                        logger.debug(f"LTI client store REDIRECT")
                        return self.client_store_redirect(request)

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
        message_launch_data = message_launch.get_launch_data()
        return message_launch_data

    def client_store_redirect(self, request):
        redirect_uri = request.build_absolute_uri()
        logger.debug(f"client store: redirect_uri: {redirect_uri}")

        if request.method == 'GET':
            redirect_uri = urljoin(redirect_uri, urlparse(redirect_uri).path)
        else:
            params = {
                'state': self.get_parameter(
                    request, 'state'),
                'authenticity_token': self.get_parameter(
                    request, 'authenticity_token'),
                'id_token': self.get_parameter(
                    request, 'id_token'),
                'utf8': self.get_parameter(
                    request, 'utf8')
            }

        url = f"{redirect_uri}?{urlencode(params)}"

        if url.startswith('http:') and request.is_secure():
            url = f"https{uri[4:]}"

        # dig oidc auth origin out of jwt
        iss = self.sniff_at_jwt('iss', params['id_token'])
        reg = get_tool_conf().find_registration_by_issuer(iss)
        auth_url = urlparse(reg.get_auth_token_url())
        auth_origin = f"{auth_url.scheme}://{auth_url.netloc}"

        logger.debug(f"client store: auth_url: {auth_origin}")
        logger.debug(f"client store: redirecting to: {url}")

        return BLTILaunchRedirect(
            url, params['state'], auth_origin).do_js_redirect()

    def sniff_at_jwt(self, key, id_token):
        parts = id_token.split('.')
        if len(parts) != 3:
            raise BLTIException("Invalid id_token")

        raw_body = DjangoMessageLaunch.urlsafe_b64decode(parts[1])
        body = json.loads(raw_body)
        return body[key] if key in body else None

    def get_parameter(self, request, key):
        params = request.POST if request.method == 'POST' else request.GET
        return params.get(key)
