# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import time
from logging import getLogger
from blti import BLTI

logger = getLogger(__name__)


def log_response_time(func):
    def wrapper(*args, **kwargs):
        self = args[0]

        start = time.time()
        try:
            val = func(*args, **kwargs)
        except Exception:
            raise
        finally:
            module = self.__module__
            function = func.__name__

            is_view_class = True
            if module == "django.core.handlers.wsgi":
                is_view_class = False

            if is_view_class:
                arg_str = str(args[2:])
            else:
                arg_str = str(args[1:])

            kw_str = str(kwargs)
            end = time.time()

            try:
                request = args[1]
                login_id = BLTI().get_session(request).get(
                    'custom_canvas_user_login_id')
            except Exception as ex:
                login_id = None

            arg_str = arg_str.replace("#", "___")
            kw_str = kw_str.replace("#", "___")

            logger.info(
                'user: {}, method: {}.{}, args: {}, kwargs: {}, '
                'time: {}'.format(
                    login_id, module, function, arg_str, kw_str, end - start))
        return val
    return wrapper
