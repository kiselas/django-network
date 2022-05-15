from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

from chats.consumers import PublicChatConsumer
from notifications.consumer import NotificationConsumer
from private_chats.consumers import ChatConsumer

application = ProtocolTypeRouter({
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path('', NotificationConsumer.as_asgi()),
                path("public_chats/<room_id>/", PublicChatConsumer.as_asgi()),
                path("chat/<room_id>/", ChatConsumer.as_asgi())
            ])
        )
    )
})