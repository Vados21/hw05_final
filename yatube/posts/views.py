from cProfile import Profile
from os import remove
import re
from webbrowser import get
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm, FollowForm
from .models import Comment, Follow, Group, Post, User
from yatube.settings import PAGINATOR_LIST
from yatube.utils import paginator_func


@cache_page(20 * 15)
def index(request):
    post_list = Post.objects.all()
    context = {
        'page_obj': paginator_func(request, post_list),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    template = 'posts/group_list.html'
    context = {
        'group': group,
        'page_obj': paginator_func(request, post_list),
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    post_counter = Paginator(post_list, PAGINATOR_LIST).count
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user).exists()
    )
    context = {
        'author': author,
        'post_counter': post_counter,
        'following': following,
        'page_obj': paginator_func(request, post_list),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    author_posts_count = post.author.posts.count()
    context = {
        'post': post,
        'author_posts_count': author_posts_count,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    context = {'form': form}

    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user).all()
    context = {
        'page_obj': paginator_func(request, post_list),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user.username == username:
        return redirect('posts:profile', username)
    following = get_object_or_404(User, username=username)
    already_follows = Follow.objects.filter(
        user=request.user,
        author=following
    ).exists()
    if not already_follows:
        Follow.objects.create(user=request.user, author=following)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    following = get_object_or_404(User, username=username)
    follower = get_object_or_404(Follow, author=following, user=request.user)
    follower.delete()
    return redirect('posts:profile', username)
