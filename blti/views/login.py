# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.views.decorators.csrf import csrf_exempt
from django.template.response import TemplateResponse
from blti.config import get_tool_conf, get_launch_data_storage
from blti.oidc_login import BLTIOIDCLogin
import logging


logger = logging.getLogger(__name__)


@csrf_exempt
def login(request):
    try:
        tool_conf = get_tool_conf()
        launch_data_storage = get_launch_data_storage()
        oidc_login = BLTIOIDCLogin(
            request, tool_conf, launch_data_storage=launch_data_storage)
        target_link_uri = getattr(request, request.method)['target_link_uri']
        js_redirect = request.GET.get('lti_storage_frame', None) is not None

        if target_link_uri.startswith('http:') and request.is_secure():
            target_link_uri = f"https:{target_link_uri[5:]}"

        return oidc_login.enable_check_cookies().redirect(
            target_link_uri, js_redirect)
    except KeyError:
        logger.error(f"Missing 'target_link_uri' in {request.method} params: "
                     "{request.body.decode('utf-8')}")
        return TemplateResponse(request, 'blti/500.html',
                                context={'error': 'Missing Target Link URI'},
                                status=500)
    except Exception as ex:
        logger.exception(f"LTI 1.3 login exception: {ex}")
        return TemplateResponse(request, 'blti/500.html',
                                context={'error': str(ex)}, status=500)
