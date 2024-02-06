# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, modes
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from base64 import b64decode, b64encode


class aes128cbc(object):
    """
    Advanced Encryption Standard object

    For reference:
    https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/
    """

    _key = None
    _iv = None

    def __init__(self, key, iv):
        if key is None:
            raise ValueError('Missing AES key')
        if iv is None:
            raise ValueError('Missing AES initialization vector')

        self._key = key.encode('utf8')
        self._iv = iv.encode('utf8')

    def encrypt(self, msg):
        msg = self._pad(self.str_to_bytes(msg))
        cipher = Cipher(AES(self._key), modes.CBC(self._iv))
        encryptor = cipher.encryptor()
        ct = encryptor.update(msg) + encryptor.finalize()
        return ct

    def decrypt(self, msg):
        cipher = Cipher(AES(self._key), modes.CBC(self._iv))
        decryptor = cipher.decryptor()
        dct = decryptor.update(msg) + decryptor.finalize()
        return self._unpad(dct).decode('utf-8')

    def _pad(self, s):
        padder = padding.PKCS7(AES.block_size).padder()
        pd = padder.update(s) + padder.finalize()
        return pd

    def _unpad(self, s):
        unpadder = padding.PKCS7(AES.block_size).unpadder()
        upd = unpadder.update(s) + unpadder.finalize()
        return upd

    def str_to_bytes(self, s):
        u_type = type(b''.decode('utf8'))
        if isinstance(s, u_type):
            return s.encode('utf8')
        return s
