from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
import json

from private_chats.models import PrivateChatRoom, PrivateChatMessage
from private_chats.utils import get_or_none, \
    calculate_timestamp, LazyRoomChatMessageEncoder
from profiles.models import Profile
from profiles.utils import LazyProfileEncoder
from private_chats.exceptions import ClientError
from django.utils import timezone
from django.core.paginator import Paginator


MSG_TYPE_MESSAGE = 0  # for standart messages
DEFAULT_NUM_MESSAGES = 10


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
            elif command == "leave":
                pass
            elif command == "send":
                if len(content['message']) != 0:
                    await self.send_room(content['room_id'], content['message'])
            elif command == "get_room_chat_messages":
                await self.display_progress_bar(True)
                room = await get_room_or_error(content['room_id'], self.scope['user'])
                payload = await get_room_chat_messages(room, content['page_number'])
                if payload:
                    payload = json.loads(payload)
                    await self.send_messages_payload(payload['messages'],
                                                     payload['new_page_number'])
                else:
                    raise ClientError(404, "Something went wrong retrieving messages")
                await self.display_progress_bar(False)
            elif command == "get_user_info":
                room = await get_room_or_error(content['room_id'], self.scope['user'])
                payload = await get_user_info(room, self.scope['user'])
                if payload:
                    payload = json.loads(payload)
                    await self.send_user_info_payload(payload['user_info'])
                else:
                    raise ClientError('EMPTY_PAYLOAD', 'Error in consumer get_user_info')

        except ClientError as e:
            await self.handle_client_error(e)

    async def disconnect(self, code):
        print('in disconnect')
        if self.room_id:
            try:
                room = await get_room_or_error(self.room_id, self.scope['user'])
            except ClientError as e:
                return await self.handle_client_error(e)

            self.room_id = None

            # remove user
            await self.channel_layer.group_discard(
                room.group_name,
                self.channel_name
            )
            # dummy json, it doesn't do anything now on client side
            await self.send_json({
                'leave': str(room.id)
            })

    async def join_room(self, room_id):
        print(f'ChatConsumer: join_room {str(room_id)}')
        try:
            room = await get_room_or_error(room_id, self.scope['user'])
        except ClientError as e:
            return await self.handle_client_error(e)

        # here we store room_id. When it's not None - we in the room
        self.room_id = room.id

        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name
        )

        await self.send_json({
            "join": str(room.id)
        })

    async def send_room(self, room_id, message):
        """
        Called by recieve_json when someone sends a message to the room
        """
        print('ChatConsumer: send_room')
        if self.room_id:
            if str(room_id) != str(self.room_id):
                raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")
        else:
            raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")
        room = await get_room_or_error(room_id, self.scope['user'])

        await create_chat_message(room, self.scope['user'], message)

        profile = await _get_user_profile(self.scope['user'])
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",
                "profile_image": profile.avatar.url,
                "profile_slug": profile.slug,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,
                "message": message,

            }
        )

    async def chat_join(self, event):
        print("ChatConsumer: chat_join")

    async def chat_leave(self, event):
        print('ChatConsumer: chat_leave')

    async def chat_message(self, event):
        """
        Called when someone send message to chat
        """
        # send a message down to the client
        ts = calculate_timestamp(timezone.now())
        await self.send_json({
            "msg_type": MSG_TYPE_MESSAGE,
            "profile_image": event["profile_image"],
            "username": event["username"],
            "user_id": event["user_id"],
            "message": event["message"],
            "profile_slug": event["profile_slug"],
            "timestamp": ts,

        })

    async def send_messages_payload(self, messages, new_page_number):
        """
        Sends a payload of messages to the UI
        :param messages:
        :param new_page_number:
        :return:
        """
        print('PublicChatConsumer: send_messages_payload')
        await self.send_json({
            "messages_payload": "messages_payload",
            "messages": messages,
            "new_page_number": new_page_number
        })

    async def send_user_info_payload(self, user_info):
        await self.send_json({
            'user_info': user_info
        })

    async def display_progress_bar(self, is_displayed):
        print(f'Display progress bar: {str(is_displayed)}')

    async def handle_client_error(self, e):
        """
        Called when a ClientError is raised when
        Send error data to the UI
        :param self:
        :param e:
        :return:
        """
        error_data = {"error": e.code}
        if e.message:
            error_data["message"] = e.message
            await self.send_json(error_data)
        return


@database_sync_to_async
def _get_user_profile(user):
    return Profile.objects.get(user=user)


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
        raise ClientError('INVALID_ROOM', 'Invalid room')

    if room.user1 == user or room.user2 == user:
        return room
    else:
        raise ClientError('PERMISSION_DENIED', 'You must be friends to chat')


@database_sync_to_async
def get_user_info(room, user):
    try:
        print('in get_user_info')
        if room.user1 == user:
            other_user = room.user2
        elif room.user2 == user:
            other_user = room.user1
        else:
            raise ClientError('USER_NOT_FOUND', 'Error in get_user_info')
        payload = {}
        other_user_profile = Profile.objects.get(user=other_user)
        s = LazyProfileEncoder()
        payload['user_info'] = s.serialize([other_user_profile])[0]

        return json.dumps(payload)
    except ClientError as e:
        print('USERINFO_ERROR', 'Error in get_user_info')
        return


@database_sync_to_async
def create_chat_message(room, user, message):
    return PrivateChatMessage.objects.create(user=user, room=room, content=message)


@database_sync_to_async
def get_room_chat_messages(room, page_number):
    try:
        qs = PrivateChatMessage.objects.by_room(room)
        p = Paginator(qs, DEFAULT_NUM_MESSAGES)
        payload = {}
        new_page_number = int(page_number)
        if new_page_number <= p.num_pages:
            new_page_number += 1
            s = LazyRoomChatMessageEncoder()
            payload['messages'] = s.serialize(p.page(page_number).object_list)
        else:
            payload['messages'] = None
        payload['new_page_number'] = new_page_number
        return json.dumps(payload)
    except Exception as e:
        print("Exception: " + str(e))