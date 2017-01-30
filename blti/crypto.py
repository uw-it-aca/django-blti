from Crypto.Cipher import AES
from base64 import b64decode, b64encode


class aes128cbc(object):

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
            self._key = key

        if iv is None:
            raise ValueError('Missing AES initialization vector')
        else:
            self._iv = iv

    def encrypt(self, msg):
        msg = self._pad(self.str_to_bytes(msg))
        crypt = AES.new(self._key, AES.MODE_CBC, self._iv)
        return b64encode(crypt.encrypt(msg)).decode('utf-8')

    def decrypt(self, msg):
        msg = b64decode(msg)
        crypt = AES.new(self._key, AES.MODE_CBC, self._iv)
        return self._unpad(crypt.decrypt(msg)).decode('utf-8')

    def _pad(self, s):
        return s + (self._bs - len(s) % self._bs) * self.str_to_bytes(chr(
            self._bs - len(s) % self._bs))

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]

    def str_to_bytes(self, s):
        u_type = type(b''.decode('utf8'))
        if isinstance(s, u_type):
            return s.encode('utf8')
        return s
