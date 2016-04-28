from django.conf.urls import patterns, url, include
from blti.views import RawBLTIView


urlpatterns = patterns(
    '',
    url(r'^$', RawBLTIView.as_view()),
)
