# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse


class TestLaunchViews(TestCase):
    def setup(self, request, *args, **kwargs):
        self.client = Client()

    def test_dev_launch_view(self):
        response = self.client.get(reverse('dev-launch'), {
            'role': 'Instructor',
            'campus': 'seattle',
        })

        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('lti-launch'))
        self.assertEqual(response.status_code, 200)
