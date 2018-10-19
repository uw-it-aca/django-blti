import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

DEBUG = True

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'blti',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.RemoteUserBackend',
]

ROOT_URLCONF = 'travis-ci.urls'

WSGI_APPLICATION = 'travis-ci.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Los_Angeles'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

CANVAS_LTI_V1_LAUNCH_PARAMS = {'oauth_consumer_key': 'XXXXXXXXXXXXXX', 'oauth_signature_method': 'HMAC-SHA1', 'oauth_timestamp': '1234567890', 'oauth_nonce': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'oauth_signature': 'XXXXXXXXXXXXXXXXXXXXXXXXXXX=', 'oauth_callback': 'about:blank', 'oauth_version': '1.0', 'launch_presentation_height': '400', 'user_image': 'https://example.instructure.com/images/thumbnails/123456/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'context_id': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'tool_consumer_info_version': 'cloud', 'ext_roles': 'urn:lti:instrole:ims/lis/Administrator,urn:lti:instrole:ims/lis/Instructor,urn:lti:instrole:ims/lis/Student,urn:lti:role:ims/lis/Instructor,urn:lti:role:ims/lis/Learner/NonCreditLearner,urn:lti:role:ims/lis/Mentor,urn:lti:sysrole:ims/lis/User', 'tool_consumer_instance_guid': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.example.instructure.com', 'context_label': 'ABC 101 A', 'lti_message_type': 'basic-lti-launch-request', 'custom_canvas_workflow_state': 'claimed', 'lis_person_name_full': 'James Average', 'context_title': 'ABC 101 A: Example Course', 'user_id': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'custom_canvas_user_id': '123456', 'launch_presentation_locale': 'en', 'custom_canvas_api_domain': 'example.instructure.com', 'custom_canvas_enrollment_state': 'active', 'tool_consumer_instance_contact_email': 'example@example.instructure.com', 'tool_consumer_info_product_family_code': 'canvas', 'custom_application_type': 'ExampleApp', 'lis_person_name_family': 'Average', 'lis_course_offering_sourcedid': '2018-spring-ABC-101-A', 'launch_presentation_width': '800', 'resource_link_title': 'Example App', 'custom_canvas_account_sis_id': 'example:account', 'lis_person_sourcedid': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'tool_consumer_instance_name': 'Example University', 'resource_link_id': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'lis_person_contact_email_primary': 'javerage@example.edu', 'roles': 'Instructor,urn:lti:instrole:ims/lis/Administrator', 'custom_canvas_course_id': '123456', 'lti_version': 'LTI-1p0', 'lis_person_name_given': 'James', 'launch_presentation_return_url': 'https://example.instructure.com/courses/123456', 'launch_presentation_document_target': 'iframe', 'custom_canvas_account_id': '12345', 'custom_canvas_user_login_id': 'javerage'}
