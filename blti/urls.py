from django.conf import settings
from django.urls import re_path
from blti.views import RawBLTIView


urlpatterns = [
    re_path(r'^$', RawBLTIView.as_view()),
]

if (getattr(settings, 'LTI_DEVELOP_APP', None)
        and getattr(settings, "DEBUG", False)):
    from blti.views.develop import BLTIDevPrepare, BLTIDevLaunch
    urlpatterns += [
        re_path(r'^dev[/]?$', BLTIDevPrepare.as_view()),
        re_path(r'^dev/launch/$', BLTIDevLaunch.as_view()),
    ]
