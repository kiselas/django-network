import timestamp as timestamp
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import timezone
from datetime import datetime
from profiles.models import Profile
from .models import PublicChatRoom, PublicRoomChatMessage
from contextlib import suppress

MSG_TYPE_MESSAGE = 0  # for standart messages

User = get_user_model()


class PublicChatConsumer(AsyncJsonWebsocketConsumer):

    @database_sync_to_async
    def _get_user_profile(self, user):
        return Profile.objects.get(user=user)

    async def connect(self):
        """
        Called when the websocket is handshaking as a part of initial connection
        """
        print("PublicChatConsumer: connect " + str(self.scope['user']))
        await self.accept()

        self.room_id = None

    async def disconnect(self, code):
        """
        Called when the Websocket closes for any reason
        """
        print("PublicChatConsumer: disconnect " + str(self.scope['user']))
        with suppress(Exception):
            if self.room_id:
                await self.leave_room(self.room_id)

    async def receive_json(self, content):
        command = content.get("command", None)
        message = content.get("message", None)
        print("PublicChatConsumer: receive_json " + str(command))
        try:
            if command == "send":
                if len(content['message'].lstrip()) == 0:
                    raise ClientError(422, "You can't send an empty message")
                else:
                    await self.send_room_message(content['room_id'], content['message'])
            elif command == "join":
                await self.join_room(content['room_id'])
            elif command == "leave":
                await self.leave_room(content['room_id'])
        except ClientError as e:
            errorData = {}
            errorData['error'] = e.code
            if e.message:
                errorData['message'] = e.message
            await self.send_json(errorData)

    async def send_room_message(self, room_id, message):
        """
        Called by receive_json when someone send a message to a room
        :param room_id:
        :param message:
        :return:
        """
        print("PublicChatConsumer: send_room_message")
        if self.room_id:
            if str(room_id) != str(self.room_id):
                raise ClientError("ROOM ACCESS DENIED", f"Room access denied, incorrect room_id")
            if not is_authenticated(self.scope['user']):
                raise ClientError("AUTH_ERROR", "You must be authenticated")

            room = await get_room_or_error(room_id)
            await create_public_chat_room_message(room, self.scope['user'], message)
            profile = await self._get_user_profile(self.scope['user'])
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

        else:
            raise ClientError("ROOM ACCESS DENIED", "Room access denied")

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

    async def join_room(self, room_id):
        """
        Called by recieve_json when someone sent a JOIN command
        :param room_id:
        :return:
        """
        print("PublicChatConsumer: join_room")

        is_auth = is_authenticated(self.scope['user'])
        if is_auth:
            try:
                room = await get_room_or_error(room_id)

                # Add user to "users" list for room
                await connect_user(room, self.scope['user'])

                self.room_id = room.id
                profile = await self._get_user_profile(self.scope['user'])
                # Add to the group so they get room messages
                await self.channel_layer.group_add(
                    room.group_name,
                    self.channel_name
                )
                await self.send_json({
                    "join": str(room.id),
                    "username": self.scope['user'].username,
                    "profile_slug": profile.slug
                })
            except ClientError as e:
                await self.handle_client_error(e)

    async def leave_room(self, room_id):
        """
        Called by recieve_json when someone sent a LEAVE command
        :param room_id:
        :return:
        """
        print("PublicChatConsumer: leave_room")

        # is_auth = is_authenticated(self.scope['user'])
        try:
            room = await get_room_or_error(room_id)

            # Remove user from "users" list
            await disconnect_user(room, self.scope['user'])
            self.room_id = None
            await self.channel_layer.group_discard(
                room.group_name,
                self.channel_name
            )
        except ClientError as e:
            await self.handle_client_error(e)

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


def is_authenticated(user):
    if user.is_authenticated:
        return True
    return False


@database_sync_to_async
def create_public_chat_room_message(room, user, message):
    return PublicRoomChatMessage.objects.create(user=user, room=room, content=message)


@database_sync_to_async
def connect_user(room, user):
    return room.connect_user(user)


@database_sync_to_async
def disconnect_user(room, user):
    return room.disconnect_user(user)


@database_sync_to_async
def get_room_or_error(room_id):
    try:
        room = PublicChatRoom.objects.get(pk=room_id)
    except PublicChatRoom.DoesNotExist:
        raise ClientError("ROOM_INVALID", "Invalid room")
    return room


class ClientError(Exception):
    def __init__(self, code, message=None):
        super().__init__(code)
        self.code = code
        self.message = message


def calculate_timestamp(timestamp):
    nd_time = naturalday(timestamp)
    if nd_time == "today" or nd_time == "yesterday":
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        str_time = str_time.strip("0")
        ts = f"{nd_time} at {str_time}"
    else:
        ts = f'{datetime.strftime(timestamp, "%m/%d/%Y")}'
    return ts
