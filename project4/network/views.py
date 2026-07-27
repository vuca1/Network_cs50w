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
        widget=forms.Textarea
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


def user(request, user_id):
    # TODO - create user's profile page
    user = get_object_or_404(User, id=user_id)

    return render(request, "network/user.html", {
        "user": user,
        "posts": Post.objects.filter(author=user_id).order_by("-timestamp")
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
