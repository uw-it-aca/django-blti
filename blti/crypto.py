from Crypto.Cipher import AES


class CryptoException(Exception):
    pass


class aes128cbc(object):

    _key = None
    _iv = None

    def __init__(self, key, iv):
        """
        Advanced Encryption Standard object

        Raises CryptoException
        """
        self._block_size = 16

        if key is None:
            raise CryptoException('Missing AES key')
        else:
            self._key = key

        if iv is None:
            raise CryptoException('Missing AES initialization vector')
        else:
            self._iv = iv

    def encrypt(self, msg):
        try:
            crypt = AES.new(self._key, AES.MODE_CBC, self._iv)
            return crypt.encrypt(msg)
        except Exception as err:
            raise CryptoException('Cannot decrypt message: ' + str(err))

    def decrypt(self, msg):
        try:
            crypt = AES.new(self._key, AES.MODE_CBC, self._iv)
            return crypt.decrypt(msg)
        except Exception as err:
            raise CryptoException('Cannot decrypt message: ' + str(err))

    def pad(self, s):
        return s + (self._block_size - len(s) % self._block_size) * chr(
            self._block_size - len(s) % self._block_size)

    def unpad(self, s):
        return s[0:-ord(s[-1])]
