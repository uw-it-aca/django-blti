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
                      redirect_origin = window.location.origin,
                      nonce = parsed_redirect.searchParams.get('nonce'),
                      state = parsed_redirect.searchParams.get('state'),
                      session_cookie_name = "{self._session_cookie_name}",
                      session_cookie_value = "{self._session_cookie_value}",
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

                function doRedirection() {
debugger
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

                function putClientData(frame) {
debugger
                    for (const prop in client_data) {
                        ltiClientStore(frame, {
                            subject: 'lti.put_data',
                            message_id: prop + '_' + state,
                            key: prop,
                            value:  client_data[prop].value
                        });
                    }
                }

                function dataStored(frame) {
                    for (const prop in client_data) {
                        if (!client_data[prop].stored) {
                            return false;
                        }
                    }
                    return true;
                }

                function ltiClientStore(frame, data) {
                    console.log("lti.put_data (" + redirect_origin + "): ", data);
                    window.parent.frames[frame].postMessage(data, redirect_origin);
                }

                function ltiClientStoreResponse(event) {
                    var message = event.data;
                    switch (message.subject) {
debugger
                        case 'lti.capabilities.response':
                            var supported = message.supported_messages;
                            for (var i = 0; i < supported.length; i++) {
                                if (supported[i].subject == "lti.put_data") {
                                    putClientData(supported[i].frame);
                                }
                            }
                        break;
                        case 'lti.put_data.response':


                            console.log("lti.get_data.response: key=" + message.key + ", value=" + message.value);
debugger


                            client_data[message.key].stored = true;
                            if (dataStored()) {
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
                    if (validClientData()) {
debugger
                        window.parent.postMessage({subject: 'lti.capabilities'}, '*');
                        setTimeout(doRedirection, 60000);
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
