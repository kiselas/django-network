import re

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.paginator import Paginator
from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType

import json

from profiles.models import Relationship
from notifications.models import Notifications, Clients
from notifications.utils import LazyNotificationEncoder
from notifications.constants import *
from private_chats.exceptions import ClientError


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Passing data to and from header.html. Notifications are displayed as "drop-downs" in the nav bar.
    There is two major categories of notifications:
        1. General Notifications
            1. FriendRequest
            2. FriendList
        1. Chat Notifications
            1. UnreadChatRoomMessages
    """

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        print("NotificationConsumer: connect: " + str(self.scope["user"]))
        print('Channel name for this user ' + self.channel_name)

        # we need to force remove duplicate channels name from db
        await remove_channel_name_from_db(user=self.scope["user"])
        # save actual channel name to db for notifications
        await save_channel_name_to_db(self.scope["user"], self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        await remove_channel_name_from_db(channel_name=self.channel_name)
        print("NotificationConsumer: disconnect")

    async def receive_json(self, content):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        command = content.get("command", None)
        try:
            if command == 'get_notifications':
                payload = await get_general_notifications(self.scope['user'], content['page_number'])
                if not payload:
                    await self.send_general_notifications_payload([], -1)
                    raise ClientError('No notifications')
                else:
                    payload = json.loads(payload)
                    await self.send_general_notifications_payload(payload['notifications'],
                                                                  payload['new_page_number'])
            elif command == 'read_notifications':
                for notification in content['notifications']:
                    notification_id = re.search(r'(\d+)', notification).group(1)
                    try:
                        await read_notification(notification_id)
                    except ClientError as e:
                        print(str(e))

        except ClientError as e:
            print('Exception: ' + str(e))
            pass

    async def display_progress_bar(self, shouldDisplay):
        print("NotificationConsumer: display_progress_bar: " + str(shouldDisplay))
        await self.send_json(
            {
                "progress_bar": shouldDisplay,
            },
        )

    async def send_general_notifications_payload(self, notifications, new_page_number):
        """
        Called by receive_json when ready to send a json array of the notifications
        """
        # print("NotificationConsumer: send_general_notifications_payload")
        await self.send_json(
            {
                "general_msg_type": GENERAL_MSG_TYPE_NOTIFICATIONS_PAYLOAD,
                "notifications": notifications,
                "new_page_number": new_page_number,
            },
        )

    # then notification for this user happens, send msg for client to update notifications
    async def new_notification_handler(self, event):
        await self.send_json(
            {
                "general_msg_type": CHAT_UPDATE_NOTIFICATION,
            },
        )


@database_sync_to_async
def read_notification(notification_id):
    try:
        notification = Notifications.objects.get(id=notification_id)
        notification.read = True
        notification.save()
        print('Successfully read notification')
    except Notifications.DoesNotExist:
        print(f'Notification with id {notification_id} does not exist')



@database_sync_to_async
def get_general_notifications(user, page_number):
    """
    Get General Notifications with Pagination (next page of results).
    This is for appending to the bottom of the notifications list.
    General Notifications are:
    1. FriendRequest
    """
    if user.is_authenticated:
        friend_request_ct = ContentType.objects.get_for_model(Relationship)
        notifications = Notifications.objects.filter(target=user).order_by(
            '-timestamp')
        p = Paginator(notifications, DEFAULT_NOTIFICATION_PAGE_SIZE)

        payload = {}
        if len(notifications) > 0 and int(page_number) <= p.num_pages:
                s = LazyNotificationEncoder()
                serialized_notifications = s.serialize(p.page(page_number).object_list)
                payload['notifications'] = serialized_notifications
                new_page_number = int(page_number) + 1
                payload['new_page_number'] = new_page_number
        else:
            return None
    else:
        raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")

    return json.dumps(payload)


@database_sync_to_async
def save_channel_name_to_db(user, channel_name):
    Clients.objects.create(user=user, channel_name=channel_name)


@database_sync_to_async
def remove_channel_name_from_db(channel_name=None, user=None):
    if channel_name:
        Clients.objects.filter(channel_name=channel_name).delete()
    if user:
        Clients.objects.filter(user=user).delete()

