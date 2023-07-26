import markdown
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse_lazy

from .models import Post


# 신디케이션 프레임워크의 Feed 클래스를 상속하여 피드를 정의
class LatestPostsFeed(Feed):
    # title,link,description 속성은 각각 <title>,<link>,<description> RSS 요소에 해당
    title = "My blog"
    link = reverse_lazy("blog:post_list")  # reverse_lazy() 유틸리티 함수는 reverse()의 지연 평가 버전
    description = "New posts of my blog."

    # items() 메서드는 피드에 포함될 객체를 검색하고 마지막 다섯개의 게시물을 가져온다.
    def items(self):
        return Post.published.all()[:5]

    def item_title(self, item):
        return item.title

    # markdown() 함수를 사용하여 마크다운 콘텐프를 HTML로 변환하고 truncatewords_html() 템플릿 필터 함수를 사용하여 게시물 설명을 30단어로 자르고 닫히지 않은 HTML 태그를 피한다.
    def item_description(self, item):
        return truncatewords_html(markdown.markdown(item.body), 30)

    def item_pubdate(self, item):
        return item.publish
