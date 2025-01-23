# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from blti.config import get_tool_conf, get_launch_data_storage
from blti.exceptions import BLTIException
from pylti1p3.contrib.django import DjangoOIDCLogin
import logging


logger = logging.getLogger(__name__)


def get_launch_url(request):
    try:
        return request.POST.get(
            'target_link_uri', request.GET['target_link_uri'])
    except KeyError:
        raise BLTIException('Missing "target_link_uri" param')


@csrf_exempt
def login(request):
    try:
        tool_conf = get_tool_conf()
        launch_data_storage = get_launch_data_storage()
        oidc_login = DjangoOIDCLogin(
            request, tool_conf, launch_data_storage=launch_data_storage)
        target_link_uri = get_launch_url(request)

        if target_link_uri.startswith('http:') and request.is_secure():
            target_link_uri = f"https:{target_link_uri[5:]}"

        return oidc_login.enable_check_cookies().redirect(target_link_uri)
    except Exception as ex:
        logger.error(f"LTI 1.3 login exception: {ex}")
        return HttpResponse(str(ex), status=401)
