
from email import message

from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.template.context_processors import request
from django.views.generic import ListView
from django.core.paginator import Paginator, PageNotAnInteger
from .forms import CommentForm, EmailPostForm
from .models import Comment, Post
from taggit.models import Tag
from django.db.models import Count
# Create your views here.


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status='published', publish__year=year,
                           publish__month=month, publish__day=day)

    # список активных коментариев для этой статьи
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        # comment was posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            #создаем обьект коментария но не сохраняем в базу
            new_comment = comment_form.save(commit=False)
            #добавляем текущую статью к коменту
            new_comment.post = post
            #сохраняем комент в базу
            new_comment.save()
    else:
        comment_form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request, 'blog/post/detail.html',{'post': post, 'comments': comments, 'new_comment': new_comment, 'comment_form': comment_form, 'similar_posts': similar_posts})


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])
    paginator = Paginator(object_list, 3) # По 3 статьи на каждой странице.
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # Если указанная страница не является целым числом.
        posts = paginator.page(1)
    except EmptyPage:
        # Если указанный номер больше, чем всего страниц, возвращаем последнюю.
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html',{'page': page,'posts': posts, 'tag': tag})

class PostListView(ListView):
    queryset = Post.published.all() # наследую поля модели пост
    context_object_name = 'posts' #для отображения этой переменной в html вместо object
    paginate_by = 3 #количество статей на страничку
    template_name = 'blog/post/list.html' # передаю шаблон странички

def post_share(request, post_id):
    # Получение статьи по идентификатору.
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
        # Форма была отправлена на сохранение.
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Все поля формы прошли валидацию.
            cd = form.cleaned_data
            # Отправка электронной почты.
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "{}"'.format(cd['name'], cd['email'], post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments:{}'.format(post.title, post_url, cd['name'], cd['comments'])
            send_mail(subject, message, 'admin@myblog.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})
