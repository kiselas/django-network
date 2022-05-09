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


    # async def send_updated_friend_request_notification(self, notification):
    #     """
    #     After a friend request is accepted or declined, send the updated notification to template
    #     payload contains 'notification' and 'response':
    #     1. payload['notification']
    #     2. payload['response']
    #     """
    #     await self.send_json(
    #         {
    #             "general_msg_type": GENERAL_MSG_TYPE_UPDATED_NOTIFICATION,
    #             "notification": notification,
    #         },
    #     )
    #
    # async def general_pagination_exhausted(self):
    #     """
    #     Called by receive_json when pagination is exhausted for general notifications
    #     """
    #     # print("General Pagination DONE... No more notifications.")
    #     await self.send_json(
    #         {
    #             "general_msg_type": GENERAL_MSG_TYPE_PAGINATION_EXHAUSTED,
    #         },
    #     )
    #
    # async def send_general_refreshed_notifications_payload(self, notifications):
    #     """
    #     Called by receive_json when ready to send a json array of the notifications
    #     """
    #     # print("NotificationConsumer: send_general_refreshed_notifications_payload: " + str(notifications))
    #     await self.send_json(
    #         {
    #             "general_msg_type": GENERAL_MSG_TYPE_NOTIFICATIONS_REFRESH_PAYLOAD,
    #             "notifications": notifications,
    #         },
    #     )
    #
    # async def send_new_general_notifications_payload(self, notifications):
    #     """
    #     Called by receive_json when ready to send a json array of the notifications
    #     """
    #     await self.send_json(
    #         {
    #             "general_msg_type": GENERAL_MSG_TYPE_GET_NEW_GENERAL_NOTIFICATIONS,
    #             "notifications": notifications,
    #         },
    #     )
    #
    # async def send_unread_general_notification_count(self, count):
    #     """
    #     Send the number of unread "general" notifications to the template
    #     """
    #     await self.send_json(
    #         {
    #             "general_msg_type": GENERAL_MSG_TYPE_GET_UNREAD_NOTIFICATIONS_COUNT,
    #             "count": count,
    #         },
    #     )
    #
    # async def send_chat_notifications_payload(self, notifications, new_page_number):
    #     """
    #     Called by receive_json when ready to send a json array of the chat notifications
    #     """
    #     # print("NotificationConsumer: send_chat_notifications_payload")
    #     await self.send_json(
    #         {
    #             "chat_msg_type": CHAT_MSG_TYPE_NOTIFICATIONS_PAYLOAD,
    #             "notifications": notifications,
    #             "new_page_number": new_page_number,
    #         },
    #     )
    #
    # async def send_new_chat_notifications_payload(self, notifications):
    #     """
    #     Called by receive_json when ready to send a json array of the notifications
    #     """
    #     await self.send_json(
    #         {
    #             "chat_msg_type": CHAT_MSG_TYPE_GET_NEW_NOTIFICATIONS,
    #             "notifications": notifications,
    #         },
    #     )
    #
    # async def chat_pagination_exhausted(self):
    #     """
    #     Called by receive_json when pagination is exhausted for chat notifications
    #     """
    #     print("Chat Pagination DONE... No more notifications.")
    #     await self.send_json(
    #         {
    #             "chat_msg_type": CHAT_MSG_TYPE_PAGINATION_EXHAUSTED,
    #         },
    #     )
    #
    # async def send_unread_chat_notification_count(self, count):
    #     """
    #     Send the number of unread "chat" notifications to the template
    #     """
    #     await self.send_json(
    #         {
    #             "chat_msg_type": CHAT_MSG_TYPE_GET_UNREAD_NOTIFICATIONS_COUNT,
    #             "count": count,
    #         },
    #     )


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

#
#
# @database_sync_to_async
# def accept_friend_request(user, notification_id):
#     """
#     Accept a friend request
#     """
#     payload = {}
#     if user.is_authenticated:
#         try:
#             notification = Notifications.objects.get(pk=notification_id)
#             friend_request = notification.content_object
#             # confirm this is the correct user
#             if friend_request.receiver == user:
#                 # accept the request and get the updated notification
#                 updated_notification = friend_request.accept()
#
#                 # return the notification associated with this FriendRequest
#                 s = LazyNotificationEncoder()
#                 payload['notification'] = s.serialize([updated_notification])[0]
#                 return json.dumps(payload)
#         except Notifications.DoesNotExist:
#             raise ClientError("AUTH_ERROR", "An error occurred with that notification. Try refreshing the browser.")
#     return None
#
#
# @database_sync_to_async
# def decline_friend_request(user, notification_id):
#     """
#     Decline a friend request
#     """
#     payload = {}
#     if user.is_authenticated:
#         try:
#             notification = Notifications.objects.get(pk=notification_id)
#             friend_request = notification.content_object
#             # confirm this is the correct user
#             if friend_request.receiver == user:
#                 # accept the request and get the updated notification
#                 updated_notification = friend_request.decline()
#
#                 # return the notification associated with this FriendRequest
#                 s = LazyNotificationEncoder()
#                 payload['notification'] = s.serialize([updated_notification])[0]
#                 return json.dumps(payload)
#         except Notifications.DoesNotExist:
#             raise ClientError("AUTH_ERROR", "An error occurred with that notification. Try refreshing the browser.")
#     return None
#
#
# @database_sync_to_async
# def refresh_general_notifications(user, oldest_timestamp, newest_timestamp):
#     """
#     Retrieve the general notifications newer than the oldest one on the screen and younger than the newest one the screen.
#     The result will be: Notifications currently visible will be updated
#     """
#     payload = {}
#     if user.is_authenticated:
#         oldest_ts = oldest_timestamp[0:oldest_timestamp.find("+")]  # remove timezone because who cares
#         oldest_ts = datetime.strptime(oldest_ts, '%Y-%m-%d %H:%M:%S.%f')
#         newest_ts = newest_timestamp[0:newest_timestamp.find("+")]  # remove timezone because who cares
#         newest_ts = datetime.strptime(newest_ts, '%Y-%m-%d %H:%M:%S.%f')
#         friend_request_ct = ContentType.objects.get_for_model(Relationship)
#         notifications = Notifications.objects.filter(target=user, content_type__in=[friend_request_ct, friend_list_ct],
#                                                     timestamp__gte=oldest_ts, timestamp__lte=newest_ts).order_by(
#             '-timestamp')
#
#         s = LazyNotificationEncoder()
#         payload['notifications'] = s.serialize(notifications)
#     else:
#         raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
#
#     return json.dumps(payload)
#
#
# @database_sync_to_async
# def get_new_general_notifications(user, newest_timestamp):
#     """
#     Retrieve any notifications newer than the newest_timestatmp on the screen.
#     """
#     payload = {}
#     if user.is_authenticated:
#         timestamp = newest_timestamp[0:newest_timestamp.find("+")]  # remove timezone because who cares
#         timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
#         friend_request_ct = ContentType.objects.get_for_model(Relationship)
#         notifications = Notifications.objects.filter(target=user, content_type__in=[friend_request_ct],
#                                                     timestamp__gt=timestamp, read=False).order_by('-timestamp')
#         s = LazyNotificationEncoder()
#         payload['notifications'] = s.serialize(notifications)
#     else:
#         raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
#
#     return json.dumps(payload)
#
#
# @database_sync_to_async
# def get_unread_general_notification_count(user):
#     payload = {}
#     if user.is_authenticated:
#         friend_request_ct = ContentType.objects.get_for_model(Relationship)
#         notifications = Notifications.objects.filter(target=user, content_type__in=[friend_request_ct])
#
#         unread_count = 0
#         if notifications:
#             for notification in notifications.all():
#                 if not notification.read:
#                     unread_count = unread_count + 1
#         payload['count'] = unread_count
#         return json.dumps(payload)
#     else:
#         raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
#
#
# @database_sync_to_async
# def mark_notifications_read(user):
#     """
#     marks a notification as "read"
#     """
#     if user.is_authenticated:
#         notifications = Notifications.objects.filter(target=user)
#         if notifications:
#             for notification in notifications.all():
#                 notification.read = True
#                 notification.save()
#     return
#
#
# @database_sync_to_async
# def get_chat_notifications(user, page_number):
#     """
#     Get Chat Notifications with Pagination (next page of results).
#     This is for appending to the bottom of the notifications list.
#     Chat Notifications are:
#     1. UnreadChatRoomMessages
#     """
#     if user.is_authenticated:
#         chatmessage_ct = ContentType.objects.get_for_model(UnreadChatRoomMessages)
#         notifications = Notifications.objects.filter(target=user, content_type=chatmessage_ct).order_by('-timestamp')
#         p = Paginator(notifications, DEFAULT_NOTIFICATION_PAGE_SIZE)
#
#         # sleep 1s for testing
#         # sleep(1)
#         print("PAGES: " + str(p.num_pages))
#         payload = {}
#         if len(notifications) > 0:
#             if int(page_number) <= p.num_pages:
#                 s = LazyNotificationEncoder()
#                 serialized_notifications = s.serialize(p.page(page_number).object_list)
#                 payload['notifications'] = serialized_notifications
#                 new_page_number = int(page_number) + 1
#                 payload['new_page_number'] = new_page_number
#                 return json.dumps(payload)
#         else:
#             return
#     else:
#         raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
#
#
# @database_sync_to_async
# def get_new_chat_notifications(user, newest_timestatmp):
#     """
#     Retrieve any notifications newer than the newest_timestatmp on the screen.
#     """
#     payload = {}
#     if user.is_authenticated:
#         timestamp = newest_timestatmp[0:newest_timestatmp.find("+")]  # remove timezone because who cares
#         timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
#         chatmessage_ct = ContentType.objects.get_for_model(UnreadChatRoomMessages)
#         notifications = Notifications.objects.filter(target=user, content_type__in=[chatmessage_ct],
#                                                     timestamp__gt=timestamp).order_by('-timestamp')
#         s = LazyNotificationEncoder()
#         payload['notifications'] = s.serialize(notifications)
#         return json.dumps(payload)
#     else:
#         raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
#
#
# @database_sync_to_async
# def get_unread_chat_notification_count(user):
#     payload = {}
#     if user.is_authenticated:
#         chatmessage_ct = ContentType.objects.get_for_model(UnreadChatRoomMessages)
#         notifications = Notifications.objects.filter(target=user, content_type__in=[chatmessage_ct])
#
#         unread_count = 0
#         if notifications:
#             unread_count = len(notifications.all())
#         payload['count'] = unread_count
#         return json.dumps(payload)
#     else:
#         raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
