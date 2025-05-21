from django.shortcuts import render, redirect
from .models import Product, Category, Profile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm
from django import forms
from django.db.models import Q
import json
from cart.cart import Cart




def search(request):
     #determine if the user has filled out the form
     if request.method == 'POST':
        searched = request.POST['searched']
    #query the database for the search term
        searched = Product.objects.filter(Q(name__icontains=searched) | Q(description__icontains=searched))
        #test for null
        if not searched:
            messages.success(request, 'No products found')



        return render (request, "search.html", {'searched': searched})
     else:

          return render(request, "search.html", {})


def update_info(request):
    if request.user.is_authenticated:
        current_user = Profile.objects.get(user__id=request.user.id)
        form = UserInfoForm(request.POST or None, instance=current_user)
    
        if form.is_valid():
            form.save()
            messages.success(request, 'Your information has been updated!')
            return redirect('home')
        return render(request, 'update_info.html', {'form': form})
    else:
        messages.error(request, 'You must be logged in to update your profile')
        return redirect('home')


def update_password(request):
    if request.user.is_authenticated:
        current_user = request.user
        if request.method == 'POST':
            # Handle form submission
            form = ChangePasswordForm(current_user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been updated successfully.')
                return redirect('update_user')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                    return redirect('update_password')
        else:
            # Display the form
            form = ChangePasswordForm(current_user)
        return render(request, 'update_password.html', {'form': form})
    else:
        messages.error(request, 'You must be logged in to update your password.')
        return redirect('login')


def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        user_form = UpdateUserForm(request.POST or None, instance=current_user)
    
        if user_form.is_valid():
            user_form.save()
            login(request, current_user)
            messages.success(request, 'User updated successfully')
            return redirect('home')
        return render(request, 'update_user.html', {'user_form': user_form})
    else:
        messages.error(request, 'You must be logged in to update your profile')
        return redirect('home')
            

def category_summary(request):
    categories = Category.objects.all()
    return render(request, 'category_summary.html', {"categories": categories})



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
            current_user = Profile.objects.get(user__id=request.user.id)
            #Get their saved cart from the database
            saved_cart = current_user.old_cart
            #covert database string back to dictionary
            if saved_cart:
                #convert to a dictionary using JSON 
                converted_cart = json.loads(saved_cart)
                # Add the loaded cart dictionary to our session
                # Get the cart
                cart = Cart(request)
                #loop through the cart and add the items from the database

                for key, value in converted_cart.items():
                    cart.db_add(product=key, quantity=value)


            
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
            messages.success(request, "User Created Successfully - Please Fill out your profile")
            return redirect('update_info')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    return render(request, 'register.html', {'form': form})