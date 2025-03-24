# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.http import HttpResponse  # type: ignore
from pylti1p3.contrib.django.redirect import DjangoRedirect


class BLTIRedirect(DjangoRedirect):
    def __init__(self, location, cookie_service=None, session_service=None):
        self._session_cookie_name = (
            f"{session_service.data_storage._prefix}"
            f"{session_service.data_storage.get_session_cookie_name()}")
        self._session_cookie_value = (
            f"{session_service.data_storage.get_session_id()}")
        super().__init__(location, cookie_service)

    def do_js_redirect(self):
        return self._process_response(
            HttpResponse(
                f"""\
                <script type="text/javascript">
                const redirect_location = "{self._location}",
                      session_cookie_name = "{self._session_cookie_name}",
                      session_cookie = "{self._session_cookie_value}";
                """
                """
                      redirect_url = URL.parse(redirect_location),
                      nonce = redirect_url.searchParams.get('nonce'),
                      state = redirect_url.searchParams.get('state'),
                      redirect_origin = redirect_url.origin;

                debugger
                function putData(frame, key, value) {
                    var data = {
                        subject: 'lti.put_data',
                        message_id: crypto.randomUUID(),
                        key: key + "_" + value,
                        value: value
                    };


                    console.log("putData key: " + key + ", value: " + value + ", frame: " + frame + ", origin: " + redirect_origin);


                    window.parent.frames[frame].postMessage(data, redirect_origin);
                }

                function ltiClientStoreResponse(event) {
                    var message = event.data;
                    switch (message.subject) {
                        case 'lti.capabilities.response':
                            var supported = message.supported_messages;
                            for (var i = 0; i < supported.length; i++) {
                                if (supported[i].subject == "lti.put_data") {
                                    var put_data_frame = supported[i].frame;
                                    putData(put_data_frame, 'nonce', nonce);
                                    putData(put_data_frame, 'state', state);
                                }
                            }
                        break;
                        case 'lti.put_data.response':
                            debugger
                            console.log("put_data response: " + message);
                        break;
                    }

                    if (message.error) {
                        console.log("event " + message.subject + " error code: " + message.error.code);
                        console.log("event " + message.subject + " error message: " + message.error.message);
                    }
                }

                function clientStoreAndRedirect() {


                    debugger


                    if (nonce && state && redirect_origin) {
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
