from django.db import models
from django.core.validators import FileExtensionValidator
from profiles.models import Profile


class Post(models.Model):
    content = models.TextField()
    page_id = models.IntegerField()
    image = models.ImageField(upload_to='posts',
                              validators=[FileExtensionValidator(['png',
                                                                  'jpg',
                                                                  'jpeg'])],
                              blank=True)
    liked = models.ManyToManyField(Profile, related_name='likes', blank=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE,
                               related_name='posts')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.content[:20])

    def num_likes(self):
        return self.liked.all().count()

    def who_liked(self):
        return self.liked.all()

    def num_comments(self):
        # через синтаксис comment (название модели) и _set
        # можем ссылаться на другие модели
        return self.comment_set.all().count()

    class Meta:
        ordering = ('-created',)


class Comment(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    body = models.TextField(max_length=1000)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.pk)


LIKE_CHOICES = (
    ('Like', 'Like'),
    ('Unlike', 'Unlike')
)


class Like(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    value = models.CharField(choices=LIKE_CHOICES, max_length=8)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}--{self.post}--{self.value}"
