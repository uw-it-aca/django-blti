# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from pylti1p3.contrib.django.redirect import DjangoRedirect


class BLTIRedirect(DjangoRedirect):
    def __init__(self, location, cookie_service=None):
        super().__init__(location, cookie_service)

    def do_js_redirect(self):
        return self._process_response(
            HttpResponse(
                """\
                <script type="text/javascript">
                const urlParams = new URLSearchParams(window.location.search),
                      nonce = urlParams.get('nonce'),
                      state = urlParams.get('state');



                console.log("param nonce:", nonce);
                console.log("param state:", state);
                debugger


                function uuidv4() {
                  return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, c =>
                    (+c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> +c / 4).toString(16)
                  );
                }

                function putData(frame, key, value, origin) {
                    var data = {
                        subject: 'lti.put_data',
                        key: key,
                        value: value,
                        message_id: uuidv4()
                    };

                    window.parent.frames[frame].postMessage(data, origin);
                }

                function ltiClientStoreResponse(event) {
                    var message = event.data;
                    switch (message.subject) {
                        case 'lti.capabilities.response':
                            var supported = message.supported_messages;
                            for (var i = 0; i < supported.length; i++) {
                                var subject = supported[i].subject;
                                if (subject == "lti.put_data") {
                                    console.log("put_data frame: " + supported[i].frame);
                                    var put_data_frame = supported[i].frame;
                                    debugger

                                }
                            }
                        break;
                    }
                }

                if (nonce && state) {
                    window.addEventListener("message", ltiClientStoreResponse);
                    window.parent.postMessage({subject: 'lti.capabilities'}, '*');
                """
                f"""
                    setTimeout(function () {{
                        window.location="{self._location}";}}, 5000);
                }} else {{
                    window.location="{self._location}";
                }}
                </script>
                """
            )
        )
