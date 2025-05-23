from django.shortcuts import render, redirect
from .models import Product, Category, Profile
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm
from django import forms
from django.db.models import Q
import json
from cart.cart import Cart
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from .tokens import account_activation_token


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully!')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('home')

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
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Save user but don't activate yet
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # Get username and email from the form
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Send activation email
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            activation_link = request.build_absolute_uri(
                reverse('activate', kwargs={'uidb64': uid, 'token': token})
            )
            send_mail(
                'Activate your account',
                f'Click the link to activate your account: {activation_link}',
                'noreply@yourdomain.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, "Check your email to activate your account.")
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})