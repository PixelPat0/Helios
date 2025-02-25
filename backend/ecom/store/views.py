from django.shortcuts import render, redirect
from .models import Product, Category
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm
from django import forms


def category(request, foo):
    # Replace Hyphens with Spaces
    foo = foo.replace('-', ' ')
    # Get the Category from the url
    try:
        # look up the category by name
        category = Category.objects.get(name=foo)
        products = Product.objects.filter(category=category)
        return render(request, 'category.html', {'products': products, 'category': category})
    except:
        messages.success(request, 'Category does not exist')
        return redirect('home')


def product(request, pk):
    product = Product.objects.get(id=pk)
    return render(request, 'product.html', {'product': product})



# Home view to display all products
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

# About view to display the about page
def about(request):
    return render(request, 'about.html')

# Login view to authenticate and log in a user
def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You are now logged in')
            return redirect('home')
        else:
            messages.success(request, 'Invalid credentials, try again')
            return redirect('login')
    return render(request, 'login.html')

# Logout view to log out a user
def logout_user(request):
    logout(request)
    messages.success(request, 'You are now logged out')
    return redirect('home')

# Register view to create a new user
def register_user(request):
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            # Authenticate and log in the user after registration
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You have successfully logged in!")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    return render(request, 'register.html', {'form': form})