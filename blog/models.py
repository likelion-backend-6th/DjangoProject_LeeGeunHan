from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

from taggit.managers import TaggableManager


# Create your models here.
class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Post(models.Model):
    # 글의 현재 상태
    class Status(models.TextChoices):
        # 임시저장 글
        DRAFT = "DF", "Draft"
        # 게시된글
        PUBLISHED = "PB", "Published"
        # Post.Status.names = ['DRAFT','PUBLISHED']

    title = models.CharField(max_length=250)
    slug = models.SlugField(
        max_length=250, allow_unicode=True, unique_for_date="publish"
    )
    body = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    tags = TaggableManager()

    status = models.CharField(
        max_length=2, choices=Status.choices, default=Status.DRAFT
    )

    # 기본매니저
    objects = models.Manager()  # 커스텀 매니저 사용할때 필수로 기본매니저도 정의
    # 사용자 정의 매니저
    published = PublishedManager()  # 사용법 Post.published.filter()

    # 장고 기본 유저 모델을 사용
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blog_posts"
    )
    # related_name -> 외래키에서 접근할때 사용할 이름

    class Meta:
        ordering = ["-publish"]
        indexes = [
            models.Index(fields=["-publish"]),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self):
        return reverse(
            "blog:post_detail",
            args=[self.publish.year, self.publish.month, self.publish.day, self.slug],
        )


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["created"]
        indexes = [
            models.Index(fields=["created"]),
        ]

    def __str__(self):
        return f"Comment by {self.name} on {self.post}"
