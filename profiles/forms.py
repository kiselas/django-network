from django import forms
from .models import Profile
from posts.models import Post, Comment


class ProfileModelForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'bio', 'avatar')


class PostModelForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'field'}))
    class Meta:
        model = Post
        fields = ('content', 'image')


class CommentModelForm(forms.ModelForm):
    label = ""
    body = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Add a comment', 'label': 'Comment'},), label="")

    class Meta:
        model = Comment
        fields = ('body',)


