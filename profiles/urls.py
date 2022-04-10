from django.urls import path
from .views import (like_unlike_post,
                    delete_update_comment, delete_update_post,
                    invites_received_view,
                    ProfileListView, ProfileDetailView,
                    send_invitation, remove_friend,
                    accept_reject_invitation
                    )

app_name = 'profiles'

urlpatterns = [
    path('liked/', like_unlike_post, name='like-post-view'),
    path('delete-update-comment/', delete_update_comment, name='delete-update-comment'),
    path('delete-update-post/', delete_update_post, name='delete-update-post'),
    path('friends/', invites_received_view, name='friends'),
    path('all-profiles/', ProfileListView.as_view(), name='all-profiles-view'),
    path('<slug>/', ProfileDetailView.as_view(), name='profile-detail-view'),
    path('send-invite', send_invitation, name='send-invite'),
    path('remove-friend', remove_friend, name='remove-friend'),
    path('accept-reject-invitation', accept_reject_invitation, name='accept-reject-invitation'),
]
