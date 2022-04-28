import uuid
from django.core.serializers.python import Serializer


def get_random_code():
    code = str(uuid.uuid4())[:8].replace('_', '').lower()
    return code


class LazyProfileEncoder(Serializer):
    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'id': str(obj.id)})
        dump_object.update({'username': str(obj.id)})
        dump_object.update({'first_name': str(obj.first_name)})
        dump_object.update({'last_name': str(obj.last_name)})
        dump_object.update({'profile_image': str(obj.avatar.url)})
        dump_object.update({'profile_slug': str(obj.slug)})
        return dump_object
