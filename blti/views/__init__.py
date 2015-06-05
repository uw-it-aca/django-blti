from django.conf import settings
from django.template import Context, loader
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from blti import BLTI

# RawBLTI
@csrf_exempt
def RawBLTI(request, template='blti/raw.html'):
    params = {
        'blti_params': None,
        'validation_error': None,
    }
    try:
        params['blti_params'] = BLTI().validate(request)
    except Exception as err:
        params['validation_error'] = '%s' % err

    t = loader.get_template(template)
    c = Context(params)
    return HttpResponse(t.render(c))
