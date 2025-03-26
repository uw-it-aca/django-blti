# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.http import HttpResponse  # type: ignore
from pylti1p3.contrib.django.redirect import DjangoRedirect
from urllib.parse import urlparse
from uuid import uuid4


class BLTIRedirect(DjangoRedirect):
    def __init__(self, location, cookie_service=None, session_service=None):
        self._session_cookie_name = (
            f"{session_service.data_storage._prefix}"
            f"{session_service.data_storage.get_session_cookie_name()}")
        self._session_cookie_value = (
            f"{session_service.data_storage.get_session_id()}")
        parsed_location = urlparse(location)
        self._origin = f"{parsed_location.scheme}://{parsed_location.netloc}"
        session_service.data_storage.set_value(
            'lti_client_store_origin', self._origin)
        self._lti_message_id = f"{uuid4()}"
        session_service.data_storage.set_value(
            'lti_client_store_messsage_id', self._origin)
        super().__init__(location, cookie_service)

    def do_js_redirect(self):
        return self._process_response(
            HttpResponse(
                f"""\
                <script type="text/javascript">
                const redirect_location = "{self._location}",
                      parsed_redirect = URL.parse(redirect_location),
                      origin = "{self._origin}",
                      nonce = parsed_redirect.searchParams.get('nonce'),
                      state = parsed_redirect.searchParams.get('state'),
                      session_cookie_name = "{self._session_cookie_name}",
                      session_cookie_value = "{self._session_cookie_value}",
                      message_id = "{self._lti_message_id}";
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
debugger
                    window.location=redirect_location;
                }

                function validClientData() {
                    for (const prop in client_data) {
                        if (!client_data[prop].value) {
                            console.log("incomplete client data: " + prop);
                            return false;
                        }
                    }

                    return true;
                }

                function clientDataMessageId(prop) {
                    return prop + '_' + message_id;
                }

                function putClientData(frame) {
                    for (const prop in client_data) {
                        ltiClientStore(frame, {
                            subject: 'lti.put_data',
                            message_id: clientDataMessageId(prop),
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
                    console.log("lti.put_data (" + origin + "): ", data);
                    window.parent.frames[frame].postMessage(data, origin);
                }

                function ltiClientStoreResponse(event) {
                    var message = event.data;
                    switch (message.subject) {
                        case 'lti.capabilities.response':
                            var supported = message.supported_messages;
                            for (var i = 0; i < supported.length; i++) {
                                if (supported[i].subject == "lti.put_data") {
                                    putClientData(supported[i].frame);
                                }
                            }
                        break;
                        case 'lti.put_data.response':
                            console.log(message.subject +
                                        ": key=" + message.key +
                                        ", value=" + message.value);
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
