# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.core.management.base import BaseCommand, CommandError
from jwcrypto.jwk import JWK
from Crypto.PublicKey import RSA
import json


KEY_LENGTH = 4096


class Command(BaseCommand):
    help = 'Generate RSA keys and JWK for JWT signing'

    def add_arguments(self, parser):
        parser.add_argument('private_key_file', type=str, nargs=1)
        parser.add_argument('public_key_file', type=str, nargs=1)
        parser.add_argument('jwt_file', type=str, nargs=1)

    def create_keys(self):
        private_key = RSA.generate(KEY_LENGTH)
        return (private_key.exportKey(format='PEM'),
                private_key.publickey().exportKey(format='PEM'))

    def create_jwk(self, public_key):
        jwk_obj = JWK.from_pem(public_key)
        public_jwk = json.loads(jwk_obj.export_public())
        public_jwk['alg'] = 'RS256'
        public_jwk['use'] = 'sig'
        return json.dumps(public_jwk)

    def handle(self, *args, **options):
        private_key, public_key = self.create_keys()
        public_jwk = self.create_jwk(public_key)

        with open(options['private_key_file'][0], 'w') as f:
            f.write(private_key.decode('utf-8'))

        with open(options['public_key_file'][0], 'w') as f:
            f.write(public_key.decode('utf-8'))

        with open(options['jwt_file'][0], 'w') as f:
            f.write(public_jwk)
