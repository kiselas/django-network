from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .models import Profile, Relationship
from posts.models import Post, Like, Comment
from .forms import ProfileModelForm, PostModelForm, CommentModelForm
from django.views.generic import UpdateView, DeleteView, ListView, DetailView
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from notifications.models import Notifications
from django.contrib.contenttypes.models import ContentType
OBJ_ID_FRIENDS_REQUESTS = 1

@login_required
def like_unlike_post(request):
    user = request.user
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        post_obj = Post.objects.get(id=post_id)
        profile = Profile.objects.get(user=user)

        if profile in post_obj.liked.all():
            post_obj.liked.remove(profile)
        else:
            post_obj.liked.add(profile)

        like, created = Like.objects.get_or_create(user=profile, post_id=post_id)

        if not created:
            if like.value == 'Like':
                like.value = 'Unlike'
            else:
                like.value = 'Like'
        else:
            like.value = 'Like'
        post_obj.save()
        like.save()

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def delete_update_post(request):
    user = request.user
    post_id = request.POST.get('post_id')
    post = Post.objects.get(id=post_id)
    if 'delete_post' in request.POST:
        if not post.author.user == user:
            messages.warning(request,
                             'You need to be the author of the comment')
        else:
            post.delete()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def delete_update_comment(request):
    user = request.user
    comment_id = request.POST.get('comment_id')
    comment = Comment.objects.get(id=comment_id)
    post_id = request.POST.get('post_id')
    if 'delete_comment' in request.POST:
        if not comment.user.user == user:
            messages.warning(request,
                             'You need to be the author of the comment')
        else:
            comment.delete()
    if 'update_comment' in request.POST:

        if not comment.user.user == user:
            messages.warning(request,
                             'You need to be the author of the comment')
        else:
            comment.body = request.POST.get("comment_body")
            comment.save()
    return redirect(request.META.get('HTTP_REFERER') + '#post-' + post_id)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'posts/confirm_del.html'
    success_url = reverse_lazy('profiles:my-profile-view')

    def get_object(self, *args, **kwargs):
        pk = self.kwargs.get('pk')
        post = Post.objects.get(pk=pk)
        if not post.author.user == self.request.user:
            messages.warning(self.request,
                             'You need to be the author of the post')
        return post


class PostUpdateView(LoginRequiredMixin, UpdateView):
    form_class = PostModelForm
    template_name = 'posts/update.html'
    success_url = reverse_lazy('profiles:my-profile-view')

    def form_valid(self, form):
        profile = Profile.objects.get(user=self.request.user)
        if form.instance.author == profile:
            return super().form_valid(form)
        else:
            form.add_error(None, "You need to be the author of the post")
            return super().form_invalid(form)


@login_required
def invites_received_view(request):
    profile = Profile.objects.get(user=request.user)
    friend_requests = Relationship.objects.invitations_received(profile)

    context = {'friend_requests': friend_requests}

    return render(request, 'profiles/friends.html', context)


@login_required
def accept_reject_invitation(request):
    if request.method == 'POST':
        pk = request.POST.get('profile_pk')
        sender = Profile.objects.get(pk=pk)
        receiver = Profile.objects.get(user=request.user)
        rel = get_object_or_404(Relationship, sender=sender, receiver=receiver)

        if rel.status == 'send':
            content_type = ContentType.objects.get_for_model(Relationship)
            if 'approve_request' in request.POST:
                rel.status = 'accepted'
                rel.save()

                # create notification
                Notifications(target=sender.user,
                              from_user=receiver.user,
                              redirect_url=f"/profiles/{receiver.slug}/",
                              verb=f"Your friend request to user {receiver.first_name} {receiver.last_name} accepted",
                              content_type=content_type,
                              object_id=OBJ_ID_FRIENDS_REQUESTS,
                              ).save()
            elif 'decline_request' in request.POST:
                rel.delete()

                # create notification
                Notifications(target=sender.user,
                              from_user=receiver.user,
                              redirect_url=f"/profiles/{receiver.slug}/",
                              verb=f"Your friend request to user {receiver.first_name} {receiver.last_name} rejected",
                              content_type=content_type,
                              object_id=OBJ_ID_FRIENDS_REQUESTS,
                              ).save()

        return redirect(request.META.get('HTTP_REFERER'))


@login_required
def profiles_list_view(request):
    user = request.user
    qs = Profile.objects.get_all_profiles(user)

    context = {'qs': qs}

    return render(request, 'profiles/profiles_list.html', context)


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'profiles/user_profile.html'
    context_object_name = 'profile'

    def get_object(self):
        slug = self.kwargs.get('slug')
        print('*'*100)
        print(slug)
        profile = Profile.objects.get(slug=slug)
        return profile

    def post(self, request, *args, **kwargs):
        user = request.user
        if 'submit_profile' in request.POST:
            profile_form = ProfileModelForm(request.POST or None,
                                            request.FILES or None,
                                            instance=Profile.objects.get(user=user))
            # profile form
            if profile_form.is_valid():
                profile_form.save()

        if 'submit_post' in request.POST:
            post_form = PostModelForm(request.POST, request.FILES)
            page_id = request.POST.get('page_id')
            if post_form.is_valid():
                instance = post_form.save(commit=False)
                instance.author = Profile.objects.filter(user=request.user).get()
                instance.page_id = page_id
                instance.save()

        elif 'submit_comment' in request.POST:
            comment_form = CommentModelForm(request.POST)
            if comment_form.is_valid():
                instance = comment_form.save(commit=False)
                instance.user = Profile.objects.filter(user=request.user).get()
                instance.post = Post.objects.get(id=request.POST.get('post_id'))
                instance.save()
                comment_form = CommentModelForm()

        elif 'delete_comment' in request.POST:
            comment_id = request.POST.get('comment_id')
            comment = Comment.objects.get(id=comment_id)
            if not comment.user.user == user:
                messages.warning(request,
                                 'You need to be the author of the comment')
            else:
                comment.delete()
        elif 'update_comment' in request.POST:
            comment_id = request.POST.get('comment_id')
            comment = Comment.objects.get(id=comment_id)
            if not comment.user.user == user:
                messages.warning(request,
                                 'You need to be the author of the comment')
            else:
                comment.body = request.POST.get("comment_body")
                comment.save()
        return redirect(request.META.get('HTTP_REFERER'))

    def get_context_data(self, **kwargs):
        # передает значения в context
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username__iexact=self.request.user)
        profile = Profile.objects.get(user=user)
        rel_r = Relationship.objects.filter(sender=profile)
        rel_s = Relationship.objects.filter(receiver=profile)
        rel_receiver = []
        rel_sender = []
        for item in rel_r:
            rel_receiver.append(item.receiver.user)
        for item in rel_s:
            rel_sender.append(item.sender.user)
        context['rel_receiver'] = rel_receiver
        context['rel_sender'] = rel_sender
        user_profile = self.get_object()
        context['posts'] = Post.objects.filter(page_id=user_profile.id)
        context['post_form'] = PostModelForm()
        context['comment_form'] = CommentModelForm()
        context['post_added'] = False
        print(profile, user_profile)
        if profile == user_profile:
            context['profile_form'] = ProfileModelForm(instance=profile)

        return context


class ProfileListView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = 'profiles/profiles_list.html'
    context_object_name = 'qs'

    def get_queryset(self):
        qs = Profile.objects.get_all_profiles(self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        # передает значения в context
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username__iexact=self.request.user)
        profile = Profile.objects.get(user=user)
        rel_r = Relationship.objects.filter(sender=profile)
        rel_s = Relationship.objects.filter(receiver=profile)
        rel_receiver = []
        rel_sender = []
        for item in rel_r:
            rel_receiver.append(item.receiver.user)
        for item in rel_s:
            rel_sender.append(item.sender.user)
        context['rel_receiver'] = rel_receiver
        context['rel_sender'] = rel_sender
        context['is_empty'] = False
        if len(self.get_queryset()) == 0:
            context['is_empty'] = True
        return context


@login_required
def send_invitation(request):
    if request.method == 'POST':
        pk = request.POST.get('profile_pk')
        user = request.user
        sender = Profile.objects.get(user=user)
        receiver = Profile.objects.get(pk=pk)

        rel = Relationship.objects.create(sender=sender,
                                          receiver=receiver,
                                          status='send')

        content_type = ContentType.objects.get_for_model(Relationship)
        Notifications(target=receiver.user,
                      from_user=sender.user,
                      redirect_url=f"/profiles/{sender.slug}/",
                      verb=f"Recieved friend request from {sender.first_name} {sender.last_name}",
                      content_type=content_type,
                      object_id=OBJ_ID_FRIENDS_REQUESTS,
                      ).save()

        return redirect(request.META.get('HTTP_REFERER'))
    return redirect('profiles:my-profile-view')


@login_required
def remove_friend(request):
    if request.method == 'POST':
        pk = request.POST.get('profile_pk')
        user = request.user
        sender = Profile.objects.get(user=user)
        receiver = Profile.objects.get(pk=pk)

        rel = Relationship.objects.get(
            (Q(sender=sender) & Q(receiver=receiver)) |
            (Q(sender=receiver) & Q(receiver=sender))
        )
        rel.delete()
        return redirect(request.META.get('HTTP_REFERER'))
    return redirect('profiles:my-profile-view')
