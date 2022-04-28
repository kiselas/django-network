import json
from itertools import chain

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from private_chats.models import PrivateChatRoom
from profiles.models import Profile
from private_chats.utils import find_or_create_private_chat


def private_chat_room_view(request, *args, **kwargs):

    user = request.user

    if not user.is_authenticated:
        return redirect('home_view')

    rooms1 = PrivateChatRoom.objects.filter(user1=user)
    rooms2 = PrivateChatRoom.objects.filter(user2=user)

    rooms = list(chain(rooms1, rooms2))

    # m_and_f - list with dicts {'message': 'last_message', 'friend': friend}
    m_and_f = []
    for room in rooms:
        # figure out which user is friend
        if room.user1 == user:
            friend = room.user2
        else:
            friend = room.user1
        friend = Profile.objects.get(user=friend)
        m_and_f.append({"message": "",
                        'friend': friend})

    context = {'debug_mode': settings.DEBUG,
               'm_and_f': m_and_f}
    return render(request, "chats/private_chats.html", context)


def create_or_return_private_chat(request, *args, **kwargs):
    user1 = request.user
    payload =  {}
    if user1.is_authenticated:
        if request.method == 'POST':
            user2_id = request.POST.get('user2_id')
            try:
                user2 = User.objects.get(pk=user2_id)
                chat = find_or_create_private_chat(user1, user2)
                payload['response'] = "Successfully got the chat"
                payload['chatroom_id'] = chat.id
            except Exception as e:
                payload['response'] = "Error happened while searching for chat"
    else:
        payload['response'] = "You can't start a chat if you not authenticated"
    return HttpResponse(json.dumps(payload), content_type='application/json')