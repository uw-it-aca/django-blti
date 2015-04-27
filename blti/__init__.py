import time
import json
import urllib
from oauth import oauth
from base64 import b64decode, b64encode
from django.conf import settings
from blti.crypto import aes128cbc


class BLTIException(Exception):
    pass


class BLTI(object):
    """
    Basic LTI Validator
    """

    def validate(self, request):
        try:
            self._oauth_server = oauth.OAuthServer(data_store=BLTIDataStore())
            self._oauth_server.add_signature_method(oauth.OAuthSignatureMethod_HMAC_SHA1())

            params = None
            body = request.read()
            if body and len(body):
                params = dict((k,v) for k,v in [tuple(map(urllib.unquote_plus, kv.split('='))) for kv in body.split('&')])
            else:
                raise BLTIException('Missing or malformed parameter or value')

            oauth_request = oauth.OAuthRequest.from_request(request.method,
                                                            request.build_absolute_uri(),
                                                            headers=request.META,
                                                            parameters=params)
            consumer = self._oauth_server._get_consumer(oauth_request)
            self._oauth_server._check_signature(oauth_request, consumer, None)
            return oauth_request.get_nonoauth_parameters()
        except oauth.OAuthError, err:
            raise BLTIException('%s' % (err.message))

    def set_session(self, request, **kwargs):
        if not request.session.exists(request.session.session_key):
            request.session.create()

        kwargs['_blti_session_id'] = request.session.session_key
        request.session['blti'] = self.encrypt_session(kwargs)
        
    def get_session(self, request):
        if 'blti' not in request.session:
            raise BLTIException('Invalid Session')

        blti_data = self.decrypt_session(request.session['blti'])
        if blti_data['_blti_session_id'] != request.session.session_key:
            raise BLTIException('Invalid BLTI session data')

        blti_data.pop('_blti_session_id', None)
        return blti_data

    def pop_session(self, request):
        if 'blti' in request.session:
            request.session.pop('blti', None)

    def encrypt_session(self, data):
        aes = aes128cbc(settings.BLTI_AES_KEY, settings.BLTI_AES_IV)
        return b64encode(aes.encrypt(aes.pad(json.dumps(data))))

    def decrypt_session(self, string):
        aes = aes128cbc(settings.BLTI_AES_KEY, settings.BLTI_AES_IV)
        return json.loads(aes.unpad(aes.decrypt(b64decode(string))))


class BLTIDataStore(oauth.OAuthDataStore):
    def __init__(self):
        self.consumers = {}
        for app_key in settings.LTI_CONSUMERS:
            self.consumers[app_key] = BLTIConsumer(app_key, settings.LTI_CONSUMERS[app_key])

    def lookup_consumer(self, key):
        return self.consumers.get(key, None)

    def lookup_nonce(self, oauth_consumer, oauth_token, nonce):
        return nonce if oauth_consumer.CheckNonce(nonce) else None


class BLTIConsumer(oauth.OAuthConsumer):
    """
    OAuthConsumer superclass that adds nonce caching
    """
    def __init__(self,key,secret):
        oauth.OAuthConsumer.__init__(self,key,secret)
        self.nonces=[]

    def CheckNonce(self,nonce):
        """Returns True if the nonce has been checked in the last hour"""
        now = time.time()
        old = now - 3600.0
        trim = 0
        for n,t in self.nonces:
            if t < old:
                trim = trim + 1
            else:
                break
        if trim:
            self.nonces = self.nonces[trim:]

        for n,t in self.nonces:
            if n == nonce:
                return True

        self.nonces.append((nonce,now))
