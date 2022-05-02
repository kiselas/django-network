from datetime import datetime
from django.contrib.humanize.templatetags.humanize import naturalday
from django.core.serializers.python import Serializer

from private_chats.models import PrivateChatRoom
from profiles.models import Profile

MSG_TYPE_MESSAGE = 0
DEFAULT_NUM_MESSAGES = 10


def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None


def find_or_create_private_chat(user1, user2):
    chat = get_or_none(PrivateChatRoom, user1=user1, user2=user2) \
           or get_or_none(PrivateChatRoom, user1=user2, user2=user1)
    if not chat:
        chat = PrivateChatRoom(user1=user1, user2=user2)
        chat.save()
    return chat


def calculate_timestamp(timestamp):
    nd_time = naturalday(timestamp)
    if nd_time == "today" or nd_time == "yesterday":
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        str_time = str_time.strip("0")
        ts = f"{nd_time} at {str_time}"
    else:
        ts = f'{datetime.strftime(timestamp, "%m/%d/%Y")}'
    return ts


class LazyRoomChatMessageEncoder(Serializer):
    def get_dump_object(self, obj):
        profile = Profile.objects.get(user=obj.user)

        dump_object = {}
        dump_object.update({'msg_type': MSG_TYPE_MESSAGE,
                            'user_id': obj.user.id,
                            'username': obj.user.username,
                            'message': obj.content,
                            "profile_image": profile.avatar.url,
                            "profile_slug": profile.slug,
                            'timestamp': calculate_timestamp(obj.timestamp),
                            })
        return dump_object
