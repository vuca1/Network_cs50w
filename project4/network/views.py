from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django import forms

import json

from .models import User, Post

class NewPostForm(forms.Form):
    content = forms.CharField(
        label="Content",
        required=True,
        max_length=500,
        widget=forms.Textarea(attrs={
            "rows": 5
        })
    )


POSTS_PER_PAGE = 10


def index(request):
    # divide to pages
    p = Paginator(
        Post.objects.all().order_by("-timestamp"),
        POSTS_PER_PAGE
    )

    page_number = request.GET.get("page") if request.GET.get("page") else 1
    page_obj = p.get_page(page_number) # get_page checks valid input

    return render(request, "network/index.html", {
        "new_post_form": NewPostForm(),
        "page_obj": page_obj,
    })


def user_profile(request, user_id):
    # get user by 'user_id'
    user = get_object_or_404(User, id=user_id)
    # check whether 'request.user' follows 'user_profile'
    if request.user.is_authenticated:
        is_following = request.user.following.filter(pk=user.pk).exists()
    else:
        is_following = False

    # divide to pages
    p = Paginator(
        Post.objects.filter(author=user_id).order_by("-timestamp"),
        POSTS_PER_PAGE
    )
    
    page_number = request.GET.get("page") if request.GET.get("page") else 1
    page_obj = p.get_page(page_number) # get_page checks valid input
    
    return render(request, "network/user.html", {
        "user_profile": user,
        "page_obj": page_obj,
        "is_following": is_following  
    })

@login_required
def edit_post(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        content = data["content"]

        post = get_object_or_404(Post, id=post_id)

        # check if user owns the edited post and if text isn't empty
        if not request.user == post.author or len(content) <= 0:
            return JsonResponse({
                "success": False
            })

        # change post content in DB
        post.content = content
        post.save()

    return JsonResponse({
        "success": True
    })

@login_required
def like(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        like = data["like"]

        post = get_object_or_404(Post, id=post_id)

        # like emojis
        PRESSED = "&#127832"
        NOT_PRESSED = "&#127833"

        # like pressed
        if like:
            likes = post.likes_count
            if request.user.liked_posts.filter(id=post_id).exists():
                request.user.liked_posts.remove(post)
                return JsonResponse({
                    "success": True,
                    "likes": likes - 1,
                    "emoji": NOT_PRESSED,
                    "likedislike": "like"
                })
            else:
                if request.user.disliked_posts.filter(id=post_id).exists():
                    request.user.disliked_posts.remove(post)
                    request.user.liked_posts.add(post)
                    return JsonResponse({
                        "success": True,
                        "likes": likes + 2,
                        "emoji": PRESSED,
                        "likedislike": "like"
                    })
                else:
                    request.user.liked_posts.add(post)
                    return JsonResponse({
                        "success": True,
                        "likes": likes + 1,
                        "emoji": PRESSED,
                        "likedislike": "like"
                    })
            
        # dislike pressed
        else:
            likes = post.likes_count
            if request.user.disliked_posts.filter(id=post_id).exists():
                request.user.disliked_posts.remove(post)
                return JsonResponse({
                    "success": True,
                    "likes": likes + 1,
                    "emoji": NOT_PRESSED,
                    "likedislike": "dislike"
                })
            else:
                if request.user.liked_posts.filter(id=post_id).exists():
                    request.user.liked_posts.remove(post)
                    request.user.disliked_posts.add(post)
                    return JsonResponse({
                        "success": True,
                        "likes": likes - 2,
                        "emoji": PRESSED,
                        "likedislike": "dislike"
                    })
                else:
                    request.user.disliked_posts.add(post)
                    return JsonResponse({
                        "success": True,
                        "likes": likes - 1,
                        "emoji": PRESSED,
                        "likedislike": "dislike"
                    })

    return JsonResponse({
        "success": False
    })
        


@login_required
def create_post(request):
    if request.method == "POST":
        new_post = NewPostForm(request.POST)

        # check form input validity
        if new_post.is_valid():
            content = new_post.cleaned_data["content"]
        else:
            return render(request, "network/index.html", {
                "new_post_form": NewPostForm(),
                "posts": Post.objects.order_by("-timestamp").all()
            })

        # create new 'Post' and save it
        new_post = Post(
            content=content,
            author=request.user
        )
        new_post.save()

    return redirect("index")


@login_required
def toggle_follow(request):
    if request.method == "POST":
        # get 'user_id' from HTML form
        user_id = request.POST.get("user_id")

        if user_id is None:
            return redirect("index")

        # get 'user' by 'user_id'
        user = get_object_or_404(User, pk=user_id)

        # if logged in user is user to follow, redirect to 'index'
        if user == request.user:
            return redirect("index")

        # follow or unfollow desired user
        if request.user.following.filter(pk=user.pk).exists():
            request.user.following.remove(user)
        else:
            request.user.following.add(user)

    return redirect("user_profile", user_id=user.id)


@login_required
def following(request):
    # render main page but only with posts from following users
    return render(request, "network/index.html", {
        "new_post_form": NewPostForm(),
        "posts": Post.objects
                    .filter(author__in=request.user.following.all())
                    .order_by("-timestamp")
    })



def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
