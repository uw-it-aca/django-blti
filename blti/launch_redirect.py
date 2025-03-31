# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.http import HttpResponse
from pylti1p3.contrib.django.redirect import DjangoRedirect
import json


class BLTILaunchRedirect(DjangoRedirect):
    def __init__(self, location, params, auth_origin):
        self._location = location
        self._params = params
        self._auth_origin = auth_origin
        super().__init__(location)

    def do_js_redirect(self):
        return self._process_response(
            HttpResponse(
                f"""\
                <script type="text/javascript">
                const redirect_location = "{self._location}",
                      parameters = {json.dumps(self._params, indent=4)},
                      redirect_origin = "{self._auth_origin}";
                """
                """\
                var client_data = {
                        nonce: null,
                        state: null,
                        session_cookie_value: null
                    };

                function doRedirection() {
                    var f = document.createElement('form');
                    f.action = redirect_location;
                    f.method = 'POST';

                    formInput(f, 'lti1p3_session_id',
                        client_data.session_cookie_value);
                    formInput(f, 'lti1p3_state',
                        client_data.state);
                    formInput(f, 'lti1p3_nonce',
                        client_data.nonce);

                    for (const p in parameters) {
                        formInput(f, p, parameters[p]);
                    }

                    document.body.appendChild(f);
                    f.submit();
                }

                function formInput(f, k, v) {
                    var i=document.createElement('input');
                    i.type='hidden';
                    i.name=k;
                    i.value=v;
                    f.appendChild(i);
                }

                function clientDataMessageId(prop) {
                    return prop + '_' + parameters.state;
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
                    window.parent.frames[frame].postMessage(
                        data, redirect_origin);
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
                    window.parent.postMessage({
                        subject: 'lti.capabilities'}, '*');
                }

                window.addEventListener("message", ltiClientStoreResponse);
                document.addEventListener("DOMContentLoaded",
                                          clientStoreAndRedirect);
                </script>
                """
            )
        )
