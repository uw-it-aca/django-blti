# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from blti.cookies_allowed_check_page import BLTICookiesAllowedCheckPage
from pylti1p3.contrib.django import DjangoOIDCLogin


class BLTIOIDCLogin(DjangoOIDCLogin):
    def get_cookies_allowed_js_check(self) -> str:
        protocol = "https" if self._request.is_secure() else "http"
        params_lst = [
            "iss",
            "login_hint",
            "target_link_uri",
            "lti_message_hint",
            "lti_deployment_id",
            "client_id",
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
