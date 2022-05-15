from django.db import models
from django.conf import settings


class PrivateChatRoom(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name='user1')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name='user2')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Chat {self.user1}-{self.user2}"

    @property
    def group_name(self):
        """
        Returns the channels group name that sockets should subscribe
        :return:
        """
        return f"PrivateChatRoom-{self.id}"


class PrivateChatMessageManager(models.Manager):
    def by_room(self, room):
        qs = PrivateChatMessage.objects.filter(room=room).order_by('-timestamp')
        return qs


class PrivateChatMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, )
    room = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False, blank=False)
    read = models.BooleanField(default=False)

    # the field where is stored the id of the user who has already read the message
    # in format 1,2,3,4
    # then all users from the chat in read_users -> field read switch to true
    # for private chat length to switch read field == 2
    # for public char length must be equal количеству человек в группе
    read_users_id = models.CharField(max_length=255, blank=True, unique=False)
    objects = PrivateChatMessageManager()

    def __str__(self):
        return self.content


class UnreadChatRoomMessages(models.Model):
    pass
