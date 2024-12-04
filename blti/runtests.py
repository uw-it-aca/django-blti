#!/usr/bin/env python

# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import django
from django.test.utils import get_runner
from django.conf import settings
import sys
import os


def load_settings():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
    django.setup()


def run_tests(*test_args):
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(test_args)
    if failures:
        sys.exit(bool(failures))


if __name__ == "__main__":
    load_settings()
    run_tests(*sys.argv[1:])
