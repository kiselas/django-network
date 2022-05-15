from django.contrib import admin
from notifications.models import Notifications, Clients


class NotificationsAdmin(admin.ModelAdmin):

    list_filter = ['content_type']
    list_display = ['target', 'content_type', 'timestamp', 'read']
    search_fields = ['target__username']

    class Meta:
        model = Notifications


class ClientsAdmin(admin.ModelAdmin):

    list_filter = ['user']
    list_display = ['user', 'channel_name']
    search_fields = ['user']

    class Meta:
        model = Clients



admin.site.register(Notifications, NotificationsAdmin)
admin.site.register(Clients, ClientsAdmin)

