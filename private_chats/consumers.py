from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
import json

from private_chats.models import PrivateChatRoom, PrivateChatMessage
from private_chats.utils import get_or_none
from profiles.models import Profile
from profiles.utils import LazyProfileEncoder


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        print(f'ChatConsumer: connect {str(self.scope["user"])}')
        await self.accept()
        self.room_id = None

    async def receive_json(self, content):

        print('ChatConsumer: receiver_json')
        command = content.get("command", None)
        try:
            if command == "join":
                await self.join_room(content['room_id'])
            if command == "leave":
                pass
            if command == "send":
                pass
            if command == "get_room_chat_messages":
                pass
            if command == "get_user_info":
                room = await get_room_or_error(content['room_id'], self.scope['user'])
                payload = await get_user_info(room, self.scope['user'])
                if payload:
                    payload = json.loads(payload)
                    await self.send_user_info_payload(payload['user_info'])
                else:
                    raise Exception('Error in consumer get_user_info')


        except Exception as e:
            print('Error in receive_json' + str(e))

    async def disconnect(self, code):
        print('ChatConsumer: disconnect')
        pass

    async def join_room(self, room_id):
        print(f'ChatConsumer: join_room {str(room_id)}')
        try:
            room = await get_room_or_error(room_id, self.scope['user'])
        except Exception as e:
            return
        await self.send_json({
            "join": str(room.id)
        })

    async def leave_room(self, room_id):
        print('ChatConsumer: leave_room')

    async def send_room(self, room_id, message):
        print('ChatConsumer: send_room')

    async def chat_join(self, event):
        print("ChatConsumer: chat_join")

    async def chat_leave(self, event):
        print('ChatConsumer: chat_leave')

    async def chat_message(self, event):
        print('ChatConsumer: chat_message')

    async def send_messages_payload(self, messages, new_page_number):
        print('ChatConsumer send_messages_payload')

    async def send_user_info_payload(self, user_info):
        await self.send_json({
            'user_info': user_info
        })

    async def display_progress_bar(self, is_displayed):
        print(f'Display progress bar: {str(is_displayed)}')


@database_sync_to_async
def get_room_or_error(room_id, user):
    """
    Tries to fetch a room for the user and check permissions.
    :param room_id:
    :param user:
    :return:
    """
    try:
        room = PrivateChatRoom.objects.get(pk=room_id)
    except Exception as e:
        raise Exception('Invalid room')

    if room.user1 == user or room.user2 == user:
        return room
    else:
        raise Exception("You must be friends to chat")


@database_sync_to_async
def get_user_info(room, user):
    # try:
    print('in get_user_info')
    if room.user1 == user:
        other_user = room.user2
    elif room.user2 == user:
        other_user = room.user1
    else:
        raise Exception('Error in get_user_info')
    payload = {}
    other_user_profile = Profile.objects.get(user=other_user)
    s = LazyProfileEncoder()
    payload['user_info'] = s.serialize([other_user_profile])[0]

    return json.dumps(payload)
    # except ZeroDivisionError as e:
    #     print('Error in get_user_info')
    #     return