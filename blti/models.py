from django.db import models


class BLTIKeyStore(models.Model):
    consumer_key = models.CharField(max_length=80, unique=True)
    shared_secret = models.CharField(max_length=80)
    added_date = models.DateTimeField(auto_now_add=True)


class BLTIData(object):
    def __init__(self, **kwargs):
        # Canvas internal IDs
        self.canvas_course_id = kwargs.get('custom_canvas_course_id')
        self.canvas_user_id = kwargs.get('custom_canvas_user_id')
        self.canvas_account_id = kwargs.get('custom_canvas_account_id')

        # SIS IDs
        self.course_sis_id = kwargs.get('lis_course_offering_sourcedid')
        self.user_sis_id = kwargs.get('lis_person_sourcedid')
        self.account_sis_id = kwargs.get('custom_canvas_account_sis_id')

        # Course attributes
        self.course_short_name = kwargs.get('context_label')
        self.course_long_name = kwargs.get('context_title')

        # User attributes
        self.user_login_id = kwargs.get('custom_canvas_user_login_id')
        self.user_full_name = kwargs.get('lis_person_name_full')
        self.user_first_name = kwargs.get('lis_person_name_given')
        self.user_last_name = kwargs.get('lis_person_name_family')
        self.user_email = kwargs.get('lis_person_contact_email_primary')
        self.user_avatar_url = kwargs.get('user_image')

        # LTI app attributes
        self.link_title = kwargs.get('resource_link_title')
        self.return_url = kwargs.get('launch_presentation_return_url')

        # Canvas hostname
        self.canvas_api_domain = kwargs.get('custom_canvas_api_domain')

        self.data = kwargs

    def get(self, name):
        return self.data.get(name)
