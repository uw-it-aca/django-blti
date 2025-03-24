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
                      parsed_redirect = URL.parse(redirect_location),
                      redirect_origin = parsed_redirect.origin;
                      nonce = parsed_redirect.searchParams.get('nonce'),
                      state = parsed_redirect.searchParams.get('state'),
                      session_cookie_name = "{self._session_cookie_name}",
                      session_cookie_value = "{self._session_cookie_value}",
                """
                """
                      clientStore = {
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

                function doRedirection() {
debugger
                    window.location=redirect_location;
                }

                function validClientData() {
                    for (const prop in clientStore) {
                        if (!clientStore[prop].value) {
                            console.log("incomplete client data: " + prop + " is missing")
                            return false;
                        }
                    }

                    return true;
                }

                function storeClientData(frame) {
                    for (const prop in clientStore) {
                        var data = {
                            subject: 'lti.put_data',
                            message_id: prop + '_' + session_cookie_value,
                            key: prop + '_' + clientStore[prop].value,
                            value:  clientStore[prop].value
                        };

                        console.log("lti.put_data : origin: " + redirect_origin + "data: ", data);

                        window.parent.frames[frame].postMessage(data, redirect_origin);
                    }
                }

                function dataStored(frame) {
                    for (const prop in clientStore) {
                        if (!clientStore[prop].stored) {
                            return false;
                        }
                    }
                    return true;
                }

                function ltiClientStoreResponse(event) {
                    var message = event.data;
                    switch (message.subject) {
                        case 'lti.capabilities.response':
                            var supported = message.supported_messages;
                            for (var i = 0; i < supported.length; i++) {
                                if (supported[i].subject == "lti.put_data") {
                                    storeClientData(supported[i].frame);
                                }
                            }
                        break;
                        case 'lti.put_data.response':
                            const prop = message.key.split('_')[0];

                            console.log("lti.put_data response: ", message);



                            clientStore[prop].stored = true;
                            if (dataStored()) {
debugger
                                doRedirection();
                            }
                        break;
                    }

                    if (message.error) {
                        console.error("event " + message.subject + 
                                      " code: " + message.error.code +
                                      " message: " + message.error.message);
                    }
                }

                function clientStoreAndRedirect() {
                    if (validClientData()) {
                        window.parent.postMessage({subject: 'lti.capabilities'}, '*');
                        setTimeout(doRedirection, 10000);
                    } else {
                        doRedirection();
                    }
                }

                window.addEventListener("message", ltiClientStoreResponse);
                document.addEventListener("DOMContentLoaded", clientStoreAndRedirect);
                </script>
                """
            )
        )
