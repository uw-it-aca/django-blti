# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import b64decode, b64encode



class aes128cbc(object):
    """
    https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/
    https://cryptography.io/en/latest/hazmat/primitives/padding/
    """

    _key = None
    _iv = None

    def __init__(self, key, iv):
        """
        Advanced Encryption Standard object
        """
        self._bs = 16  # Block size

        if key is None:
            raise ValueError('Missing AES key')
        else:
            self._key = key.encode('utf8')

        if iv is None:
            raise ValueError('Missing AES initialization vector')
        else:
            self._iv = iv.encode('utf8')

    def encrypt(self, msg):
        cipher = Cipher(algorithms.AES256(self._key), modes.CBC(self._iv))
        encryptor = cipher.encryptor()
        msg = self._pad(self.str_to_bytes(msg))
        ct = encryptor.update(msg) + encryptor.finalize()
        return ct

    def decrypt(self, msg):
        msg = b64decode(msg)
        cipher = Cipher(algorithms.AES(self._key), modes.CBC(self._iv))
        decryptor = cipher.decryptor()
        dct = decryptor.update(msg) + decryptor.finalize()
        return self._unpad(dct).decode('utf-8')

    def _pad(self, s):
        padder = padding.PKCS7(self._bs).padder()
        return padder.update(s) + padder.finalize()

        #return s + (self._bs - len(s) % self._bs) * self.str_to_bytes(chr(
        #    self._bs - len(s) % self._bs))

    def _unpad(self, s):
        unpadder = padding.PKCS7(self._bs).unpadder()
        return unpadder.update(padded_data) + unpadder.finalize()
        #return s[:-ord(s[len(s)-1:])]

    def str_to_bytes(self, s):
        u_type = type(b''.decode('utf8'))
        if isinstance(s, u_type):
            return s.encode('utf8')
        return s
