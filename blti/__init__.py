import json
from base64 import b64decode, b64encode
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from blti.crypto import aes128cbc


class BLTIException(Exception):
    pass


class BLTI(object):
    def __init__(self):
        if not hasattr(settings, 'BLTI_AES_KEY'):
            raise ImproperlyConfigured('Missing setting BLTI_AES_KEY')
        if not hasattr(settings, 'BLTI_AES_IV'):
            raise ImproperlyConfigured('Missing setting BLTI_AES_IV')

    def set_session(self, request, **kwargs):
        if not request.session.exists(request.session.session_key):
            request.session.create()

        kwargs['_blti_session_id'] = request.session.session_key
        request.session['blti'] = self._encrypt_session(kwargs)

    def get_session(self, request):
        if 'blti' not in request.session:
            raise BLTIException('Invalid Session')

        blti_data = self._decrypt_session(request.session['blti'])
        if blti_data['_blti_session_id'] != request.session.session_key:
            raise BLTIException('Invalid BLTI session data')

        blti_data.pop('_blti_session_id', None)
        return blti_data

    def pop_session(self, request):
        if 'blti' in request.session:
            request.session.pop('blti', None)

    def _encrypt_session(self, data):
        aes = aes128cbc(settings.BLTI_AES_KEY, settings.BLTI_AES_IV)
        return aes.encrypt(json.dumps(data))

    def _decrypt_session(self, string):
        aes = aes128cbc(settings.BLTI_AES_KEY, settings.BLTI_AES_IV)
        return json.loads(aes.decrypt(string))
