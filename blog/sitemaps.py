from django.contrib.sitemaps import Sitemap

from .models import Post


# 사용자 정의 사이트맵
class PostSitemap(Sitemap):
    # 페이지의 변경 빈도
    changefreq = "weekly"
    # 사이트 내에서의 상대적인 중요도
    priority = 0.9

    # 사이트맵에 포함될 객체의 쿼리셋 반환
    def items(self):
        return Post.published.all()

    # 각 객체의 URL을 직접 지정하려면 사이트맵 클래스에 location 메서드를 추가할 수 있다.

    # items()에 반환된 객체를 받아 해당 객체가 마지막으로 수정된 시간을 반환
    def lastmod(self, obj):
        return obj.updated
