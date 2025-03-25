# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.http import HttpResponse
from pylti1p3.contrib.django.redirect import DjangoRedirect


class BLTILaunchRedirect(DjangoRedirect):
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
                      parsed_redirect = URL.parse(redirect_location),
                      redirect_origin = parsed_redirect.origin,
                      nonce,
                      state = parsed_redirect.searchParams.get('state'),
                      session_cookie_name,
                      session_cookie_value,
                """
                """
                      client_data = {
                          nonce: {
                              value: nonce,
                              stored: false
                          },
                          state: {
                              value: state,
                              stored: false
                          },
                          session_cookie_name: {
                              value: session_cookie_name,
                              stored: false
                          },
                          session_cookie_value: {
                              value: session_cookie_value,
                              stored: false
                          }
                     };

debugger
                function doRedirection() {
                    window.location=redirect_location;
                }

                function validClientData() {
                    for (const prop in client_data) {
                        if (!client_data[prop].value) {
                            console.log("incomplete client data: " + prop + " is missing");
                            return false;
                        }
                    }

                    return true;
                }

                function getClientData(frame) {
                    for (const prop in client_data) {
                        ltiClientStore(frame, {
                            subject: 'lti.get_data',
                            message_id: prop + '_' + state,
                            key: prop + '_' + state
                        });
                    }
                }

                function dataFetched(frame) {
                    for (const prop in client_data) {
                        if (!client_data[prop].value) {
                            return false;
                        }
                    }
                    return true;
                }

                function ltiClientStore(frame, data) {
                    window.parent.frames[frame].postMessage(data, redirect_origin);
                }

                function ltiClientStoreResponse(event) {
                    var message = event.data;
                    switch (message.subject) {
                        case 'lti.capabilities.response':
                            var supported = message.supported_messages;
                            for (var i = 0; i < supported.length; i++) {
                                if (supported[i].subject == "lti.get_data") {
                                    getClientData(supported[i].frame);
                                }
                            }
                        break;
                        case 'lti.get_data.response':
debugger
                            const underscore = message.key.lastIndexOf('_');
                            const prop = (underscore > 0) ? message.key.slice(0, underscore) : message.key;

                            client_data[prop].value = message.value;
                            if (dataFetched()) {
                                doRedirection();
                            }
                        break;
                    }

                    if (message.error) {
                        console.error("event " + message.subject + 
                                      ": error:  code: " + message.error.code +
                                      " message: " + message.error.message);
                    }
                }

                function clientStoreAndRedirect() {
                    window.parent.postMessage({subject: 'lti.capabilities'}, '*');
                    setTimeout(doRedirection, 10000);
                }

                window.addEventListener("message", ltiClientStoreResponse);
                document.addEventListener("DOMContentLoaded", clientStoreAndRedirect);
                </script>
                """
            )
        )
