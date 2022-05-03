from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, Relationship
from private_chats.utils import find_or_create_private_chat


@receiver(post_save, sender=User)
def post_save_create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=Relationship)
def post_save_add_to_friends(sender, instance, created, **kwargs):
    sender_ = instance.sender
    receiver_ = instance.receiver
    if instance.status == 'accepted':
        sender_.friends.add(receiver_.user)
        receiver_.friends.add(sender_.user)
        sender_.save()
        receiver_.save()
        chat = find_or_create_private_chat(user1=receiver_.user,
                                           user2=sender_.user)
        if not chat.is_active:
            chat.is_active = True
            chat.save()

@receiver(pre_delete, sender=Relationship)
def pre_delete_from_friends(sender, instance, **kwargs):
    sender = instance.sender
    receiver = instance.receiver
    sender.friends.remove(receiver.user)
    receiver.friends.remove(sender.user)
    sender.save()
    receiver.save()
    chat = find_or_create_private_chat(user1=receiver.user,
                                       user2=sender.user)
    if chat.is_active:
        chat.is_active = False
        chat.save()