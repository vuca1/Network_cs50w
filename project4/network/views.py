from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
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

def index(request):
    return render(request, "network/index.html", {
        "new_post_form": NewPostForm(),
        "posts": Post.objects.all().order_by("-timestamp")
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


def user_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    is_following = request.user.following.filter(pk=user.pk).exists()
    
    return render(request, "network/user.html", {
        "user_profile": user,
        "posts": Post.objects.filter(author=user_id).order_by("-timestamp"),
        "is_following": is_following  
    })


@login_required
def toggle_follow(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")

        if user_id is None:
            return redirect("index")

        user = get_object_or_404(User, pk=user_id)

        if user == request.user:
            return redirect("index")

        if request.user.following.filter(pk=user.pk).exists():
            request.user.following.remove(user)
        else:
            request.user.following.add(user)

    return redirect("user_profile", user_id=user.id)


@login_required
def following(request):
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
