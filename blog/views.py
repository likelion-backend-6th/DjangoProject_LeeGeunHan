from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.db.models import Count  # Django ORM의 Count 집계 함수
from taggit.models import Tag
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchVector  # 여러 필드에 대한 검색을 해주는 모듈
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity

from .models import Post
from .forms import EmailPostForm, CommentForm, SearchForm

# Create your views here.


def post_list(request, tag_slug=None):
    post_list = Post.published.all()

    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    # 페이지당 3개의 게시물로 페이지네이션
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get("page", 1)

    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger or TypeError:
        # page_number가 정수가 아닌 경우 첫 번째 페이지 제공
        posts = paginator.page(1)
    except EmptyPage:
        # page_number가 범위를 벗어난 경우 결과의 마지막 페이지 제공
        posts = paginator.page(paginator.num_pages)
    return render(request, "blog/post/list.html", {"posts": posts, "tag": tag})


# def post_detail(request, id):
#     try:
#         post = Post.published.get(id=id)
#     except Post.DoesNotExist:
#         raise Http404("No Post found.")
#     return render(request, "blog/post/detail.html", {"post": post})


def post_detail(request, year, month, day, slug):
    post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=slug,
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )

    comments = post.comments.filter(active=True)
    form = CommentForm()

    # 현재 포스트의 태그를 기준으로 검색 values_list() 쿼리셋은 주어진 필드의 값을 튜플로 반환, flat=True 는 튜플을 (1,)과같은 원소가 아닌 1과 같은 단일값을 얻는다.
    post_tags_ids = post.tags.values_list("id", flat=True)

    # 태그중 하나라도 포함된 모든 포스터를 가져오며 현재 포스트는 제외
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)

    # Count 집계 함수를 사용하여 공유 태그 수를 나타내는 calculated 필드인 same_tags를 생성
    # 공유 태그 수로 정렬 후 수가 같다면 최근 포스트를 먼저 표시하며 결과는 4개만 출력
    similar_posts = similar_posts.annotate(same_tags=Count("tags")).order_by(
        "-same_tags", "-publish"
    )[:4]

    return render(
        request,
        "blog/post/detail.html",
        {
            "post": post,
            "comments": comments,
            "form": form,
            "similar_posts": similar_posts,
        },
    )


def post_share(request, post_id):
    # id로 글 검색
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == "POST":
        # 폼 제출
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # 폼 필드가 유효한 경우
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']}님이 {post.title}을(를) 추천합니다."
            message = f"{post.title}을(를) 다음에서 읽어보세요.\n\n {cd['name']}의 의견 : {cd['comments']} \n\n {cd['name']}님의 email 주소 : {cd['email']}"
            send_mail(
                subject, message, f"{cd['name']}<1@1>", [cd["to"]]
            )  # cd['email] 불필요 구글 smtp 등로고딘 구글 계정만 보낸사람으로 나옴 email 칸에 아무리 다른걸 써도 smtp 구글 계정만 보낸사람으로 출력
            sent = True
    else:
        form = EmailPostForm()
    return render(
        request, "blog/post/share.html", {"post": post, "form": form, "sent": sent}
    )


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(
        request,
        "blog/post/comment.html",
        {"post": post, "form": form, "comment": comment},
    )


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if "query" in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            results = (
                Post.published.annotate(
                    similarity=TrigramSimilarity("title", query),
                )
                .filter(similarity__gt=0.1)
                .order_by("-similarity")
            )
            # 형태소 추출 후 SearchRank를 사용하여 결과를 관련성에 따라 순위 지정
            # 제목 검색 벡터에 가중치 'A'를 적용하고 본문 검색 벡터에 가중치 'B'를 적용
            # 제목 일치는 본문 일치보다 우선하며, 결과를 필터링하여 순위가 0.3보다 높은 결과만 표시

    return render(
        request,
        "blog/post/search.html",
        {"form": form, "query": query, "results": results},
    )


class PostListView(ListView):
    queryset = Post.published.all().order_by("-updated")
    context_object_name = "posts"
    paginate_by = 3
    template_name = "blog/post/list.html"
