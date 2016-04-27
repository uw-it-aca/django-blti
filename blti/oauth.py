from django.conf import settings
from blti.models import BLTIKeyStore
from oauth import oauth
import time


class BLTIDataStore(oauth.OAuthDataStore):
    """
    Implments model- and settings-based OAuthDataStores
    """
    def lookup_consumer(self, key):
        try:
            model = BLTIKeyStore.objects.get(consumer_key=key)
            return BLTIConsumer(key, model.shared_secret)

        except BLTIKeyStore.DoesNotExist:
            try:
                consumers = getattr(settings, 'LTI_CONSUMERS', {})
                return BLTIConsumer(key, consumers[key])
            except KeyError:
                return None

    def lookup_nonce(self, oauth_consumer, oauth_token, nonce):
        return nonce if oauth_consumer.CheckNonce(nonce) else None


class BLTIConsumer(oauth.OAuthConsumer):
    """
    OAuthConsumer superclass that adds nonce caching
    """
    def __init__(self, key, secret):
        oauth.OAuthConsumer.__init__(self, key, secret)
        self.nonces = []

    def CheckNonce(self, nonce):
        """
        Returns True if the nonce has been checked in the last hour
        """
        now = time.time()
        old = now - 3600.0
        trim = 0
        for n, t in self.nonces:
            if t < old:
                trim = trim + 1
            else:
                break
        if trim:
            self.nonces = self.nonces[trim:]

        for n, t in self.nonces:
            if n == nonce:
                return True

        self.nonces.append((nonce, now))


def validate(request, params={}):
    oauth_server = oauth.OAuthServer(data_store=BLTIDataStore())
    oauth_server.add_signature_method(
        oauth.OAuthSignatureMethod_HMAC_SHA1())

    oauth_request = oauth.OAuthRequest.from_request(
        request.method,
        request.build_absolute_uri(),
        headers=request.META,
        parameters=params
    )

    if oauth_request:
        consumer = oauth_server._get_consumer(oauth_request)
        oauth_server._check_signature(oauth_request, consumer, None)
        return oauth_request.get_nonoauth_parameters()

    raise oauth.OAuthError('Invalid OAuth Request')
