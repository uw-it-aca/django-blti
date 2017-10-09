from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'^blti/', include('blti.urls')),
]
