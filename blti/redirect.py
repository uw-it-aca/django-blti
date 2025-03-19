# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from pylti1p3.contrib.django.redirect import DjangoRedirect


class BLTIRedirect(DjangoRedirect):
    def __init__(self, location, cookie_service=None):
        super().__init__(location, cookie_service)

    def do_js_redirect(self):
        return self._process_response(
            HttpResponse(
                """\
                <script type="text/javascript">
                const urlParams = new URLSearchParams(window.location.search);

                console.log("param nonce:", urlParams.get('nonce'));
                console.log("param state:", urlParams.get('state'));


                """
                f'window.location="{self._location}";'
                """\
                </script>
                """
            )
        )
