# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from blti.views.launch import BLTILaunchView


class TestLaunchViews(TestCase):
    def setup(self, request, *args, **kwargs):
        self.client = Client()

    def test_dev_launch_view(self):
        response = self.client.get(reverse('dev-launch'), {
            'role': 'Instructor',
            'campus': 'seattle',
        }, secure=True)

        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('lti-launch'), secure=True)
        self.assertEqual(response.status_code, 200)

    @patch('blti.views.launch.BLTILaunchView._login_origin_from_iss')
    def test_client_store_redirect(self, mocked):
        mocked.return_value = 'https://example.com'
        response = self.client.post(reverse('lti-launch-data'), {
            'state': 'state-ac00bf57-bdd7-47c8-8b95-918f94797aef',
            'authenticity_token': 'T1o1dHJVeGNKRXhsTnh0eGRLCg==',
            'id_token': 'MmZQdHZZSFcwd084RjAxZ1BlUUkwTVpZWXhDa1Uza2JDMmxSCg==',
            'utf8': '✓',
            'lti_storage_target': 'client_store'
        }, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'getClientData')
        self.assertContains(response, 'ltiClientStoreResponse')
        self.assertContains(response, 'doRedirection')
