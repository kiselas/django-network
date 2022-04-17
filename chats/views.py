from django.shortcuts import render
from django.conf import settings


def public_chats_view(request):
    context = {
        'debug_mode': settings.DEBUG,
        'room_id': 1
    }
    return render(request, "chats/public_chats.html", context)
