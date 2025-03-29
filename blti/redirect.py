# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.http import HttpResponse  # type: ignore
from pylti1p3.contrib.django.redirect import DjangoRedirect
from urllib.parse import urlparse, parse_qs
from uuid import uuid4


class BLTIRedirect(DjangoRedirect):
    def __init__(self, location, cookie_service=None, session_service=None):
        self._session_cookie_value = (
            f"{session_service.data_storage.get_session_id()}")
        self._location = location
        super().__init__(location, cookie_service)

    def do_js_redirect(self):
        return self._process_response(
            HttpResponse(
                f"""\
                <script type="text/javascript">
                const redirect_location = "{self._location}",
                      parsed_location = URL.parse(redirect_location),
                      parsed_params = parsed_location.searchParams,
                      origin = parsed_location.origin,
                      nonce = parsed_params.get('nonce'),
                      state = parsed_params.get('state'),
                      session_cookie_value = "{self._session_cookie_value}";
                """
                """
                var client_data = {
                        nonce: {
                            value: nonce,
                            stored: false
                        },
                        state: {
                            value: state,
                            stored: false
                        },
                        session_cookie_value: {
                            value: session_cookie_value,
                            stored: false
                        }
                    };

                function doRedirection() {
                    window.location=redirect_location;
                }

                function validClientData() {
                    for (const prop in client_data) {
                        if (!client_data[prop].value) {
                            return false;
                        }
                    }

                    return true;
                }

                function clientDataMessageId(prop) {
                    return prop + '_' + state;
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
                            client_data[message.key].stored = true;
                            if (dataStored()) {
                                doRedirection();
                            }
                        break;
                    }

                    if (message.error) {
                        console.error("event error:" + message.subject +
                                      ", code: " + message.error.code +
                                      ", message: " + message.error.message);
                    }
                }

                function clientStoreAndRedirect() {
                    if (validClientData()) {
                        window.parent.postMessage(
                             {subject: 'lti.capabilities'}, '*');
                        setTimeout(doRedirection, 5000);
                    } else {
                        doRedirection();
                    }
                }

                window.addEventListener("message", ltiClientStoreResponse);
                document.addEventListener(
                    "DOMContentLoaded", clientStoreAndRedirect);
                </script>
                """
            )
        )
