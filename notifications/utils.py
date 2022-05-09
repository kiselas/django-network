from django.core.serializers.python import Serializer
from django.contrib.humanize.templatetags.humanize import naturaltime
from profiles.models import Profile


class LazyNotificationEncoder(Serializer):
    """
    Serialize notifications into JSON
    Now there are 2 types
    1. Friend requests(send/add/delete)
    2. Unread chat room messages
    """
    def get_dump_object(self, obj):
        from_user_profile = Profile.objects.get(user=obj.from_user)
        from_user_name = f'{from_user_profile.first_name} {from_user_profile.last_name}'
        from_user_slug = from_user_profile.slug
        from_user_img = from_user_profile.avatar.url
        dump_object = {}
        dump_object.update({'notification_type': str(obj.content_type)})
        dump_object.update({'notification_id': str(obj.id)})
        dump_object.update({'verb': str(obj.verb)})
        dump_object.update({'is_read': obj.read})
        dump_object.update({'natural_timestamp': str(naturaltime(obj.timestamp))})
        dump_object.update({'timestamp': str(obj.timestamp)})
        dump_object.update({'redirect_url': str(obj.redirect_url)})
        dump_object.update({'from_user_name': from_user_name})
        dump_object.update({'from_user_slug': from_user_slug})
        dump_object.update({'from_user_img': from_user_img})
        return dump_object
