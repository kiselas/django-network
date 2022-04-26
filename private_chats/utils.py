from private_chats.models import PrivateChatRoom


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
