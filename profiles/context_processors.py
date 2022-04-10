from .models import Profile, Relationship


def profile_avatar(request):
    if request.user.is_authenticated:
        profile_obj = Profile.objects.get(user=request.user)
        profile_avatar = profile_obj.avatar
        return {'avatar': profile_avatar}
    return {}


def friend_requests(request):
    if request.user.is_authenticated:
        profile_obj = Profile.objects.get(user=request.user)
        friend_req_count = Relationship.objects.invitations_received(receiver=profile_obj).count()
        return {'friend_req_count': friend_req_count}
    return {}
