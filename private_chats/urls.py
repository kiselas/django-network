from django.urls import path

from private_chats.views import private_chat_room_view

app_name = "private_chats"

urlpatterns = [
    path("", private_chat_room_view, name="private-chat-room")
]