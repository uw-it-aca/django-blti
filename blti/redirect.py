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
                          'nonce_' + nonce: {
                              value: nonce,
                              stored: false
                          },
                          'state_' + state: {
                              value: state,
                              stored: false
                          },
                          session_cookie_name: {
                              value: "{self._session_cookie_name}",
                              stored: false
                          },
                          session_cookie: {
                              value: "{self._session_cookie_value}",
                              stored: false
                           }
                     };

                function doRedirection() {
debugger
                    window.location=redirect_location;
                }

                function storeData(frame) {
                    for (const key in clientStore) {
                        putData(put_data_frame, key, clientStore[key].value);
                        clientStore[key].stored = true;
                    }
                }

                function dataStored(frame) {
                    for (const key in clientStore) {
                        if (!clientStore[key].stored) {
                            return false;
                        }
                    }
                    return true;
                }

                function putData(frame, key, value) {
                    var data = {
                        subject: 'lti.put_data',
                        message_id: key + '_' + session_cookie_value,
                        key: key,
                        value: value
                    };

                    console.log("putData: " + data.key + 
                                " = " + data.value + 
                                ", msg_id: " + data.message_id + 
                                ", frame: " + frame + 
                                ", origin: " + redirect_origin);

                    window.parent.frames[frame].postMessage(data, redirect_origin);
                }

                function ltiClientStoreResponse(event) {
                    var message = event.data;
                    switch (message.subject) {
                        case 'lti.capabilities.response':
                            var supported = message.supported_messages;
                            for (var i = 0; i < supported.length; i++) {
                                if (supported[i].subject == "lti.put_data") {
                                    storeData(supported[i].frame);
                                }
                            }
                        break;
                        case 'lti.put_data.response':
                            clientStore[messsage.key].stored = true;
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
                    if (nonce && state && redirect_origin && session_cookie_value) {
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
