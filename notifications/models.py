from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect


class Notifications(models.Model):
    # target to send notification
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # user who created notification
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  null=True, blank=True, related_name='from_user')
    redirect_url = models.CharField(max_length=500, null=True,
                                    unique=False, blank=True,
                                    help_text="The URL to redirect when clicked notification")
    # Description of notification
    verb = models.CharField(max_length=255, unique=False, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return self.verb

    def get_content_object_type(self):
        return str(self.content_object.get_cname)


class Clients(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    channel_name = models.CharField(max_length=500, unique=True)

    def __str__(self):
        return f'{self.user}:{self.channel_name}'
