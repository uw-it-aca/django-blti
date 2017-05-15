from django.conf.urls import url
from blti.views import RawBLTIView


urlpatterns = [
    url(r'^$', RawBLTIView.as_view()),
]
