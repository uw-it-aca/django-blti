# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.http import HttpResponse
from pylti1p3.contrib.django.redirect import DjangoRedirect


class BLTILaunchRedirect(DjangoRedirect):
    def __init__(self, location, state, auth_origin):
        self._location = location
        self._state = state
        self._auth_origin = auth_origin
        super().__init__(location)

    def do_js_redirect(self):
        return self._process_response(
            HttpResponse(
                f"""\
                <script type="text/javascript">
                const redirect_location = encodeURI("{self._location}"),
                      redirect_origin = "{self._auth_origin}",
                      state = "{self._state}",
                      parsed_redirect = URL.parse(redirect_location),
                      parsed_params = parsed_redirect.searchParams;
                """
                """\
                var client_data = {
                        nonce: null,
                        state: null,
                        session_cookie_value: null
                    };

                function doRedirection() {
                    var body = {
                        lti1p3_session_cookie: client_data.session_cookie_value,
                        lti1p3_state: client_data.state,
                        lti1p3_nonce: client_data.nonce
                    };

                    for (const [k, v] of parsed_params) {
                        body[k] = v;
                    }
debugger
                    fetch("https://jsonplaceholder.typicode.com/todos", {
                      method: "POST",
                      body: JSON.stringify(body),
                      headers: {
                        "Content-type": "application/json; charset=UTF-8"
                      }
                    });
/*
                    var f = document.createElement('form');
                    f.method = 'POST';

                    f.appendChild(formInput('lti1p3_session_id', client_data.session_cookie_value));
                    f.appendChild(formInput('lti1p3_state', client_data.state));
                    f.appendChild(formInput('lti1p3_nonce', client_data.nonce));

                    for (const [k, v] of parsed_params) {
                        f.appendChild(formInput(k, v));
                    }

                    document.body.appendChild(f);

                    parsed_redirect.search = '';
                    parsed_redirect.hash = '';
                    f.action = parsed_redirect.toString();
                    f.submit();
*/
                }

                function formInput(k, v) {
                    var i=document.createElement('input');
                    i.type='hidden';
                    i.name=k;
                    i.value=v;
                    return i;
                }

                function validClientData() {
                    for (const prop in client_data) {
                        if (!client_data[prop]) {
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
                        if (!client_data[prop]) {
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

                            client_data[message.key] = message.value;
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
                }

                window.addEventListener("message", ltiClientStoreResponse);
                document.addEventListener("DOMContentLoaded", clientStoreAndRedirect);
                </script>
                """
            )
        )
