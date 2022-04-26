from django.shortcuts import render, redirect
from django.conf import settings

from private_chats.models import PrivateChatRoom, PrivateChatMessage

def private_chat_room_view(request, *args, **kwargs):

    user = request.user

    if not user.is_authenticated:
        return redirect('home_view')

    context = {'debug_mode': settings.DEBUG}

    return render(request, "chats/private_chats.html", context)
