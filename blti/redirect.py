# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.http import HttpResponse  # type: ignore
from pylti1p3.contrib.django.redirect import DjangoRedirect


class BLTIRedirect(DjangoRedirect):
    def __init__(self, location, cookie_service=None):
        super().__init__(location, cookie_service)

    def do_js_redirect(self):
        return self._process_response(
            HttpResponse(
                f"""\
                <script type="text/javascript">
                const redirect_location="{self._location}",
                """
                """

                      redirect_url = URL.parse(redirect_location),
                      redirect_domain = redirect_url.hostname,
                      nonce = redirect_url.searchParams.get('nonce'),
                      state = redirect_url.searchParams.get('state');



                console.log("param nonce:", nonce);
                console.log("param state:", state);


                function putData(frame, key, value) {
                    var data = {
                        subject: 'lti.put_data',
                        key: key,
                        value: value,
                        message_id: crypto.randomUUID()
                    };


                    debugger
                    console.log("postMessage origin " + redirect_domain + " data: " + data);


                    window.parent.frames[frame].postMessage(data, redirect_domain);
                }

                function ltiClientStoreResponse(event) {
                    var message = event.data;
                    switch (message.subject) {
                        case 'lti.capabilities.response':
                            var supported = message.supported_messages;
                            for (var i = 0; i < supported.length; i++) {
                                if (supported[i].subject == "lti.put_data") {
                                    var put_data_frame = supported[i].frame;
                                    putData(put_data_frame, 'nonce', nonce, redirect_domain);
                                    putData(put_data_frame, 'state', nonce, redirect_domain);
                                }
                            }
                        break;
                    }
                }

                function clientStoreAndRedirect() {
                    debugger
                    if (nonce && state && redirect_domain) {
                        window.parent.postMessage({subject: 'lti.capabilities'}, '*');
                        setTimeout(function () {
                            window.location=redirect_location;
                        }, 10000);
                    } else {
                        window.location=redirect_location;
                    }
                }

                window.addEventListener("message", ltiClientStoreResponse);
                document.addEventListener("DOMContentLoaded", clientStoreAndRedirect);
                </script>
                """
            )
        )
