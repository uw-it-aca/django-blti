# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.http import HttpResponse
from pylti1p3.contrib.django.redirect import DjangoRedirect
import logging


logger = logging.getLogger(__name__)


class BLTILaunchRedirect(DjangoRedirect):
    def __init__(self, location, state, auth_origin):
        logger.info(f"BLTILaunchRedirect: location={location}, "
                    f"state={state}, auth_origin={auth_origin}")
        self._location = location
        self._state = state
        self._auth_origin = auth_origin
        super().__init__(location)

    def _js_script(self):
        s = f"""\
                <script type="text/javascript">
                const redirect_location = "{self._location}",
                      redirect_origin = "{self._auth_origin}",
                      state = "{self._state}",
                      parsed_redirect = URL.parse(redirect_location),
                      parsed_params = parsed_redirect.searchParams;
                """
                """
                var client_data = {
                        nonce: {
                            value: null
                        },
                        state: {
                            value: state
                        },
                        session_cookie_name: {
                            value: null
                        },
                        session_cookie_value: {
                            value: null
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
                    return prop + '_' + state;
                }

                function getClientData(frame) {
                    for (const prop in client_data) {
                        ltiClientStore(frame, {
                            subject: 'lti.get_data',
                            message_id: clientDataMessageId(prop),
                            key: prop
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
                    console.log("lti.get_data (" + redirect_origin + "): ", data);
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


                            console.log(message.subject +
                                        ": key=" + message.key +
                                        ", value=" + message.value);

                            client_data[message.key].value = message.value;
                            if (dataFetched()) {
                                doRedirection();
                            }
                        break;
                    }

                    if (message.error) {
                        console.error("event " + message.subject + 
                                      " error (" + message.error.code +
                                      "): " + message.error.message);
                    }
                }

                function clientStoreAndRedirect() {
                    window.parent.postMessage({subject: 'lti.capabilities'}, '*');
                    setTimeout(doRedirection, 60000);
                }

                window.addEventListener("message", ltiClientStoreResponse);
                document.addEventListener("DOMContentLoaded", clientStoreAndRedirect);
                </script>
                """
        logger.info(f"js_script: {s}")
        return s

    def do_js_redirect(self):
        return self._process_response(
            HttpResponse(self._js_script(), content_type="text/html")
        )
