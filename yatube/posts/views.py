from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def paginator(request, posts):
    paginator = Paginator(posts, settings.POST_NUMBER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    post_list = Post.objects.all()
    context = {
        'page_obj': paginator(request, post_list)
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'page_obj': paginator(request, posts),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user_obj = get_object_or_404(User, username=username)
    user_posts = user_obj.posts.all()
    posts_number = user_posts.count()
    current_user = request.user
    if current_user.is_authenticated:
        following = user_obj.following.filter(user=current_user.id).exists()
    else:
        following = None
    context = {
        'page_obj': paginator(request, user_posts),
        'user_obj': user_obj,
        'posts_number': posts_number,
        'following': following,
        'current_user': current_user
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_obj = get_object_or_404(Post, pk=post_id)
    comments = post_obj.comments.all()
    form = CommentForm(request.POST or None,)
    context = {
        'post_obj': post_obj,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user.username)
    form = PostForm()
    context = {'form': form}
    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    post_obj = get_object_or_404(Post, pk=post_id)
    if post_obj.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post_obj,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {'form': form, 'post_obj': post_obj}
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post_obj = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post_obj
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__following__user=request.user
    )
    context = {
        'page_obj': paginator(request, post_list)
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            author=author,
            user=request.user
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_obj = Follow.objects.filter(
        user=request.user.id, author=author.id
    )
    if request.user != author and follow_obj.exists():
        follow_obj.delete()
    return redirect('posts:profile', username)
