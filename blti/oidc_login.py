# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from blti.redirect import BLTIRedirect
from blti.cookies_allowed_check import BLTICookiesAllowedCheckPage
from pylti1p3.request import Request
from pylti1p3.contrib.django import DjangoOIDCLogin
from pylti1p3.contrib.django.request import DjangoRequest
from pylti1p3.contrib.django.cookie import DjangoCookieService


class BLTIOIDCLogin(DjangoOIDCLogin):
    def __init__(
        self,
        request,
        tool_config,
        session_service=None,
        cookie_service=None,
        launch_data_storage=None,
    ):
        django_request = (
            request if isinstance(
                request, Request) else DjangoRequest(request)
        )
        cookie_service = (
            cookie_service if (
                cookie_service) else DjangoCookieService(django_request)
        )
        super().__init__(
            django_request,
            tool_config,
            session_service,
            cookie_service,
            launch_data_storage,
        )

    def get_cookies_allowed_js_check(self) -> str:
        protocol = "https" if self._request.is_secure() else "http"
        params_lst = [
            "iss",
            "login_hint",
            "target_link_uri",
            "lti_message_hint",
            "lti_deployment_id",
            "client_id",
            "lti_storage_target"
        ]
        additional_login_params = self.get_additional_login_params()
        params_lst.extend(additional_login_params)

        params = {"lti1p3_new_window": "1"}
        for param_key in params_lst:
            param_value = self._get_request_param(param_key)
            if param_value:
                params[param_key] = param_value

        page = BLTICookiesAllowedCheckPage(
            params,
            protocol,
            self._cookies_unavailable_msg_main_text,
            self._cookies_unavailable_msg_click_text,
            self._cookies_check_loading_text,
        )

        return page.get_html()

    def get_redirect(self, url):
        return BLTIRedirect(
            url, cookie_service=self._cookie_service,
            session_service=self._session_service)
