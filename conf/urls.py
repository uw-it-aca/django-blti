from django.conf.urls import include, url

urlpatterns = [
    url(r'^blti/', include('blti.urls')),
]
