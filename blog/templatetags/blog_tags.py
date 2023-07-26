from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe

import markdown

from ..models import Post

register = template.Library()


@register.simple_tag
def total_posts():
    return Post.published.count()


@register.inclusion_tag("blog/post/latest_posts.html")  # 반환된 값을 사용하여 렌더링될 템플릿 지정
def show_latest_posts(
    count=5,
):  # {% show_latest_posts count %} count를 이용해 표시할 포스트 수를 지정할 수 있다. default 값은 5
    latest_posts = Post.published.order_by("-publish")[:count]
    return {"latest_posts": latest_posts}


@register.simple_tag
def get_most_commented_posts(count=5):
    return Post.published.annotate(total_comments=Count("comments")).order_by(
        "-total_comments"
    )[:count]
    # annotate() 함수를 사용하여 각 포스트에 대한 총 댓글 수를 집계
    # Count 집계함수를 이용해 각 Post 객체에 계산된 total_comments 필드에 댓글 수를 저장


@register.filter(name="markdown")
def markdown_format(text):
    return mark_safe(markdown.markdown(text))

    # mark_safe 함수를 사용하여 결과를 HTML로 표시 ( Django는 어떤 HTML 코드도 신뢰하지 않고 출력하기전에 이스케이프 처리하기 때문)
