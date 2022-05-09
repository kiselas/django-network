from asgiref.sync import async_to_sync

from notifications.models import Notifications, Clients
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer


@receiver(post_save, sender=Notifications)
def post_save_friends_notification(sender, instance, created, **kwargs):
    print('hello')
    if created:
        channel_layer = get_channel_layer()
        try:
            channel_name = Clients.objects.filter(user=instance.target)[0].channel_name
            async_to_sync(channel_layer.send)(
                channel_name,
                {
                    'type': 'new_notification_handler',
                    'message': 'Insufficient Amount to Play',
                    'status': '400'
                }
            )
        except Exception:
            print('Something went wrong')

