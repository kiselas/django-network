import content as content
from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from profiles.models import Profile, Relationship

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

        # Add to the group
        await self.channel_layer.group_add(
            "public_chatroom_1",
            self.channel_name
        )

    async def disconnect(self, code):
        """
        Called when the Websocket closes for any reason
        """
        print("PublicChatConsumer: disconnect " + str(self.scope['user']))
        pass

    async def receive_json(self, content):
        command = content.get("command", None)
        message = content.get("message", None)
        print("PublicChatConsumer: receive_json " + str(command))
        print("PublicChatConsumer: receive_json " + str(message))
        try:
            if command == "send":
                if len(content['message'].lstrip()) == 0:
                    raise ClientError(422, "You can't send an empty message")
                else:
                    await self.send_message(content['message'])
        except ClientError as e:
            errorData = {}
            errorData['error'] = e.code
            if e.message:
                errorData['message'] = e.message
            await self.send_json(errorData)

    async def send_message(self, message):
        profile = await self._get_user_profile(self.scope['user'])
        await self.channel_layer.group_send(
            "public_chatroom_1",
            {
                "type": "chat.message",
                "profile_image": profile.avatar.url,
                "profile_slug": profile.slug,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,
                "message": message,

            }
        )

    async def chat_message(self, event):
        """
        Called when someone send message to chat
        """
        # send a message down to the client
        await self.send_json({
            "msg_type": MSG_TYPE_MESSAGE,
            "profile_image": event["profile_image"],
            "username": event["username"],
            "user_id": event["user_id"],
            "message": event["message"],
            "profile_slug": event["profile_slug"],

        })


class ClientError(Exception):
    def __init__(self, code, message=None):
        super().__init__(code)
        self.code = code
        self.message = message
