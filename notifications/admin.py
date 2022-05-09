from django.contrib import admin
from notifications.models import Notifications


class NotificationsAdmin(admin.ModelAdmin):

    list_filter = ['content_type']
    list_display = ['target', 'content_type', 'timestamp', 'read']
    search_fields = ['target__username']

    class Meta:
        model = Notifications


admin.site.register(Notifications, NotificationsAdmin)

