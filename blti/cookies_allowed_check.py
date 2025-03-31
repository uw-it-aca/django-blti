# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from pylti1p3.cookies_allowed_check import CookiesAllowedCheckPage
from html import escape
import json


class BLTICookiesAllowedCheckPage(CookiesAllowedCheckPage):
    def get_js_block(self) -> str:
        js_block = """\
        var siteProtocol = '%s';
        var urlParams = %s;
        var htmlEntities = {
            "&lt;": "<",
            "&gt;": ">",
            "&amp;": "&",
            "&quot;": '"',
            "&#x27;": "'"
        };

        function unescapeHtmlEntities(str) {
            for (var htmlCode in htmlEntities) {
                str = str.replace(
                    new RegExp(htmlCode, "g"), htmlEntities[htmlCode]);
            }
            return str;
        }

        function getUpdatedUrl(lti_storage_frame) {
            var newSearchParams = [];
            for (var key in urlParams) {
                if (window.location.search.indexOf(key + '=') === -1) {
                    newSearchParams.push(key + '=' + encodeURIComponent(
                        unescapeHtmlEntities(urlParams[key])));
                }
            }
            if (lti_storage_frame) {
                newSearchParams.push('lti_storage_frame=' +
                                     encodeURIComponent(lti_storage_frame));
            }
            var searchParamsStr = newSearchParams.join('&');
            if (window.location.search !== '') {
                searchParamsStr = window.location.search +
                    '&' + searchParamsStr;
            } else {
                searchParamsStr = '?' + searchParamsStr;
            }
            return window.location.protocol + '//' + window.location.hostname +
                (window.location.port ? (":" + window.location.port) : "") +
                window.location.pathname + searchParamsStr;
        }

        function displayLoadingBlock() {
            document.getElementById(
                "lti1p3-loading-msg").style.display = "block";
        }

        function displayWarningBlock() {
            document.getElementById(
                "lti1p3-warning-msg").style.display = "block";
            var newTabLink = document.getElementById("lti1p3-new-tab-link");
            var contentUrl = getUpdatedUrl();
            newTabLink.onclick = function() {
                window.open(contentUrl , '_blank');
                newTabLink.parentNode.removeChild(newTabLink);
            };
        }

        function checkCookiesAllowed() {
            var cookie = "lti1p3_test_cookie=1; path=/";
            if (siteProtocol === 'https') {
                cookie = cookie + '; Partitioned; SameSite=None; Secure';
            }

            document.cookie = cookie;
            var res = document.cookie.indexOf("lti1p3_test_cookie") !== -1;
            if (res) {
                // remove test cookie and reload page
                document.cookie = "lti1p3_test_cookie=1; " +
                                  "expires=Thu, 01-Jan-1970 00:00:01 GMT";
                displayLoadingBlock();
                window.location.href = getUpdatedUrl();
            } else if ('lti_storage_target' in urlParams) {
                var frame = urlParams.lti_storage_target;

                displayLoadingBlock();
                window.location.href = getUpdatedUrl(frame);
            } else {
                displayWarningBlock();
            }
        }

        document.addEventListener("DOMContentLoaded", checkCookiesAllowed);
        """
        # pylint: disable=deprecated-method
        js_block = js_block % (
            self._protocol,
            json.dumps({k: escape(v, True) for k, v in self._params.items()}),
        )
        return js_block
