from django.conf import settings
from django.template import Context, loader
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from blti import BLTI, BLTIException

# RawBLTI
@csrf_exempt
def RawBLTI(request, template='blti/raw.html'):
    blti_data = {}
    validation_error = None
    status_code = 200
    try:
        blti_data = BLTI().validate(request)
    except BLTIException, err:
        validation_error = str(err.message)
        template = 'blti/fail.html'
        status_code = 401
    except Exception, err:
        validation_error = str(err.message)
        template = 'blti/fail.html'
        status_code = 400

    t = loader.get_template(template)
    c = Context({
            'STATIC_URL': settings.STATIC_URL,
            'LTI_PARAMS': blti_data,
            'VALIDATION_ERROR': validation_error
    })
    return HttpResponse(t.render(c), status=status_code)
