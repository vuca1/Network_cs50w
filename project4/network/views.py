from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django import forms

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

# TODO: adapt pagenation for every "post" page
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
    is_following = request.user.following.filter(pk=user.pk).exists()

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
