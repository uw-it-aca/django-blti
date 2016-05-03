from django.db import models


class BLTIKeyStore(models.Model):
    consumer_key = models.CharField(max_length=80, unique=True)
    shared_secret = models.CharField(max_length=80)
    added_date = models.DateTimeField(auto_now_add=True)
