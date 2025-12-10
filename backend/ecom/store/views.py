# store/views.py
"""
Cleaned store views for Helios.
Replace your existing store/views.py with this (backup first).
"""

from decimal import Decimal
import json
from django.conf import settings
from django.http import JsonResponse # <-- ADDED: Needed for AJAX endpoint
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q, Sum

from cart.cart import Cart
from .models import Product, Category, Profile, QuoteRequest
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm, QuoteRequestForm

# Import newsletter form + models and notification model from payment app
from payment.forms import NewsletterSubscriberForm, ShippingForm
from payment.models import NewsletterSubscriber, Notification, Seller, ImpactFundTransaction
from payment.models import ShippingAddress # This import is crucial and now required

# Tokens for activation
from .tokens import account_activation_token


User = get_user_model()


def contact(request):
    """
    Contact page with form and business information
    """
    # You can add contact form handling here later
    return render(request, 'contact.html')

# -------------------------
# Notifications / Newsletter
# -------------------------
@login_required
def notifications_list_view(request):
    """
    Show full list of notifications for logged-in user.
    Mark currently displayed notifications as read (MVP behaviour).
    """
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark displayed notifications read
    # Optimization: Only update if there are unread ones to save DB queries
    if user_notifications.filter(is_read=False).exists():
        user_notifications.filter(is_read=False).update(is_read=True)
        
    return render(request, 'store/notifications_list.html', {'notifications': user_notifications})

@login_required
def notification_open(request, pk):
    """
    Handles clicking a single notification in the dropdown.
    Marks it as read and redirects the user.
    """
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    # Mark as read
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    # Logic to decide where to go. 
    # For MVP, if the message mentions a Quote, go to quote list.
    if 'quote' in notification.message.lower():
        # Ensure 'quote_request_list' URL exists in your urls.py, otherwise fallback
        try:
            return redirect('quote_request_list') 
        except:
            # Fallback if the quote_request_list URL name hasn't been defined yet
            messages.info(request, "Quote request functionality coming soon!") 
            pass 
            
    # FIXED: Redirect uses the correct URL name defined in store/urls.py
    return redirect('notifications_list')

@login_required
def notification_redirect_view(request, notif_id):
    """Backward-compatible wrapper — just call notification_open."""
    # The wrapper exists because some templates used this name earlier.
    return notification_open(request, notif_id)


@login_required
def mark_all_notifications_read(request):
    """Mark all unread notifications for the current user as read (POST only)."""
    # NOTE: This view is now consolidated from payment/views.py
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=400)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'ok': True})

def newsletter_subscribe(request):
    """
    Accept newsletter subscription POST and redirect back to referrer.
    """
    if request.method != 'POST':
        return redirect('home')

    form = NewsletterSubscriberForm(request.POST)
    # Determine safe redirect target
    referer_url = request.META.get('HTTP_REFERER', '/')
    DISRUPTIVE_PAGES = ['cart_summary', 'checkout', 'process_order']
    should_redirect_home = any(page in referer_url for page in DISRUPTIVE_PAGES)
    redirect_to = 'home' if should_redirect_home else referer_url

    if form.is_valid():
        try:
            form.save()
            messages.success(request, "Success! Thank you for subscribing to the Helios Project Newsletter.")
        except Exception:
            messages.warning(request, "It looks like you are already subscribed!")
        return redirect(redirect_to)
    else:
        messages.error(request, "Please enter a valid email address.")
        return redirect(redirect_to)

# -------------------------
# Donation / Public Impact
# -------------------------
def donation_page_view(request):
    """Placeholder public donation page."""
    # You will later include payment processing form/logic here.
    return render(request, 'donation_page.html', {})


def public_impact_view(request):
    """
    Public impact dashboard:
      - count of active sellers
      - total funds collected (ImpactFundTransaction.sum)
      - number of installations (manual for now)
      - newsletter form
    """
    try:
        seller_count = Seller.objects.filter(is_active=True).count()
    except Exception:
        seller_count = 0

    # Sum transactions (expenses can be negative)
    try:
        # Filter by is_active=True
        funds_collected_result = ImpactFundTransaction.objects.filter(is_active=True).aggregate(total=Sum('amount'))
        total_funds_collected = funds_collected_result['total'] or Decimal('0.00')
    except Exception:
        total_funds_collected = Decimal('0.00')

    # number_of_installations kept manual for MVP
    number_of_installations = 20

    # A sample project goal (update this to your real target)
    PROJECT_GOAL = Decimal('100000.00')

    # calculate progress percentage safely
    try:
        progress_raw = (Decimal(total_funds_collected) / PROJECT_GOAL) * Decimal('100.00') if PROJECT_GOAL > 0 else Decimal('0')
        progress_percentage = int(min(progress_raw, Decimal('100.00')).quantize(Decimal('1')))  # integer percent
    except Exception:
        progress_percentage = 0

    newsletter_form = NewsletterSubscriberForm()

    context = {
        'seller_count': seller_count,
        'total_funds_collected': total_funds_collected,
        'number_of_installations': number_of_installations,
        'progress_percentage': progress_percentage,
        'newsletter_form': newsletter_form,
    }
    return render(request, 'public_impact.html', context)


# -------------------------
# Seller public profile
# -------------------------
def seller_profile_public(request, pk):
    """
    Public seller profile and products listing.
    """
    try:
        seller = Seller.objects.get(pk=pk, is_active=True)
    except Seller.DoesNotExist:
        messages.error(request, 'Seller not found or profile is inactive.')
        return redirect('home')

    products = Product.objects.filter(seller=seller, is_available=True, is_sale=False).order_by('-id')
    sale_products = Product.objects.filter(seller=seller, is_available=True, is_sale=True).order_by('-id')

    return render(request, 'seller_profile_public.html', {
        'seller': seller,
        'products': products,
        'sale_products': sale_products,
    })


# -------------------------
# Account activation / Auth helpers
# -------------------------
def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully!')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('home')


# -------------------------
# Search / Profile / Misc
# -------------------------
def search(request):
    if request.method == 'POST':
        searched = request.POST.get('searched', '').strip()
        results = Product.objects.filter(Q(name__icontains=searched) | Q(description__icontains=searched))
        if not results.exists():
            messages.success(request, 'No products found')
        return render(request, "search.html", {'searched': results})
    return render(request, "search.html", {})


@login_required
def update_info(request):
    """
    Update Profile and ShippingInfo for logged-in users.
    """
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to update your profile')
        return redirect('home')

    # 1. Fetch the user's Profile instance
    current_user = get_object_or_404(Profile, user=request.user) 
    
    # 2. Get or create the ShippingAddress instance
    shipping_address, created = ShippingAddress.objects.get_or_create(user=request.user)

    # 3. Initialize Forms
    form = UserInfoForm(request.POST or None, request.FILES or None, instance=current_user)
    shipping_form = ShippingForm(request.POST or None, instance=shipping_address) # Use the fetched instance

    # 4. Handle POST Request
    if form.is_valid() and shipping_form.is_valid():
        form.save()
        shipping_form.save()
        messages.success(request, 'Your information has been updated!')
        return redirect('home')

    # 5. Render Template
    return render(request, 'update_info.html', {'form': form, 'shipping_form': shipping_form})


def update_password(request):
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to update your password.')
        return redirect('login')

    current_user = request.user
    if request.method == 'POST':
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
        form = ChangePasswordForm(current_user)
    return render(request, 'update_password.html', {'form': form})


def update_user(request):
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to update your profile')
        return redirect('home')

    current_user = get_object_or_404(User, id=request.user.id)
    
    # Removed redundant import (already at the top)
    shipping_user, _ = ShippingAddress.objects.get_or_create(user=request.user)

    user_form = UpdateUserForm(request.POST or None, instance=current_user)
    shipping_form = ShippingForm(request.POST or None, instance=shipping_user)

    if user_form.is_valid() and shipping_form.is_valid():
        user_form.save()
        shipping_form.save()
        login(request, current_user)
        messages.success(request, 'User updated successfully')
        return redirect('home')

    return render(request, 'update_user.html', {'user_form': user_form, 'shipping_form': shipping_form})


# -------------------------
# Category / Product / Home / Auth
# -------------------------
def category_summary(request):
    categories = Category.objects.all()
    return render(request, 'category_summary.html', {"categories": categories})


def category(request, foo):
    foo = foo.replace('-', ' ')
    try:
        category = Category.objects.get(name=foo)
        products = Product.objects.filter(category=category)
        return render(request, 'category.html', {'products': products, 'category': category})
    except Category.DoesNotExist:
        messages.success(request, 'Category does not exist')
        return redirect('home')


def product_view(request, pk):
    product = get_object_or_404(Product, id=pk)
    return render(request, 'product.html', {'product': product})



def store_home(request):
    """Store home page - displays featured products."""
    # Use is_available instead of is_active
    products = Product.objects.filter(is_available=True).order_by('-id')[:8]
    
    context = {
        'products': products,
        'page_title': 'Solar Products Store - HELIOS',
    }
    return render(request, 'store.html', context)

# Update the existing home function to redirect to store
def home(request):
    """Home page is now solutions - redirect to store for legacy links."""
    return store_home(request) 


def solutions_view(request):
    """
    Solutions page showing residential, commercial, agricultural solar solutions
    """
    return render(request, 'solutions.html')

def about(request):
    """
    About page with impact data merged from public_impact
    """
    try:
        seller_count = Seller.objects.filter(is_active=True).count()
    except Exception:
        seller_count = 0

    # Sum transactions (expenses can be negative)
    try:
        funds_collected_result = ImpactFundTransaction.objects.filter(is_active=True).aggregate(total=Sum('amount'))
        total_funds_collected = funds_collected_result['total'] or Decimal('0.00')
    except Exception:
        total_funds_collected = Decimal('0.00')

    # number_of_installations kept manual for MVP
    number_of_installations = 20

    # A sample project goal (update this to your real target)
    PROJECT_GOAL = Decimal('100000.00')

    # calculate progress percentage safely
    try:
        progress_raw = (Decimal(total_funds_collected) / PROJECT_GOAL) * Decimal('100.00') if PROJECT_GOAL > 0 else Decimal('0')
        progress_percentage = int(min(progress_raw, Decimal('100.00')).quantize(Decimal('1')))  # integer percent
    except Exception:
        progress_percentage = 0

    newsletter_form = NewsletterSubscriberForm()

    context = {
        'seller_count': seller_count,
        'total_funds_collected': total_funds_collected,
        'number_of_installations': number_of_installations,
        'progress_percentage': progress_percentage,
        'newsletter_form': newsletter_form,
    }
    return render(request, 'about.html', context)


def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # restore saved cart if present in Profile.old_cart
            try:
                current_user_profile = Profile.objects.get(user__id=request.user.id)
                saved_cart = current_user_profile.old_cart
                if saved_cart:
                    converted_cart = json.loads(saved_cart)
                    cart = Cart(request)
                    for key, value in converted_cart.items():
                        cart.db_add(product=key, quantity=value)
            except Exception:
                pass
            messages.success(request, 'You are now logged in')
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials, try again')
            return redirect('login')
    return render(request, 'login.html')


def logout_user(request):
    logout(request)
    messages.success(request, 'You are now logged out')
    return redirect('home')


def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            email = form.cleaned_data.get('email')
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            activation_link = request.build_absolute_uri(reverse('activate', kwargs={'uidb64': uid, 'token': token}))
            send_mail(
                'Activate your account',
                f'Click the link to activate your account: {activation_link}',
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@helios.example'),
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


# ---------------------------------------------------------
# QUOTE REQUEST VIEW
# ---------------------------------------------------------

def request_quote(request):
    """
    Handle quote requests from customers/prospects.
    Admin will be notified when a new quote request is submitted.
    """
    if request.method == 'POST':
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            quote_request = form.save(commit=False)
            
            # Link to authenticated user if available
            if request.user.is_authenticated:
                quote_request.buyer = request.user
            
            quote_request.save()

            # --- 1. NOTIFY ADMINS (Navbar Bell) ---
            # Get all superusers (admins)
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    message=f"New Quote Request from {quote_request.contact_name}",
                    quote_request=quote_request  # Link the specific quote object
                )
            
            # Notify admin via email
            try:
                send_mail(
                    subject='New Quote Request Submitted',
                    message=f"""
A new quote request has been submitted!

Customer Information:
- Name: {quote_request.contact_name}
- Email: {quote_request.contact_email}
- Phone: {quote_request.contact_phone}
- Location: {quote_request.location_city}, {quote_request.location_province}

Project Details:
- Project Type: {quote_request.get_project_type_display()}
- System Type: {quote_request.get_system_type_display()}
- Daily Energy Usage: {quote_request.daily_energy_usage_kwh} kWh
- Current Voltage: {quote_request.current_voltage or 'Not specified'}
- Roof Type: {quote_request.roof_type or 'Not specified'}
- Appliances: {quote_request.appliances_to_run}
- Budget Range: {quote_request.budget_range or 'Not specified'}
- Timeline: {quote_request.get_timeline_display()}

Additional Notes:
{quote_request.additional_notes or 'None'}

Quote Request ID: {quote_request.id}
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email for admin_email, _ in settings.ADMINS],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending admin notification: {e}")
            
            messages.success(request, 'Your quote request has been submitted successfully! We will get back to you soon.')
            return redirect('home')
    else:
        form = QuoteRequestForm()
        # Pre-fill with user info if authenticated
        if request.user.is_authenticated:
            form.initial = {
                'contact_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'contact_email': request.user.email,
            }
    
    return render(request, 'store/request_quote.html', {'form': form})


@login_required
def quote_request_details(request, quote_request_id):
    """
    Display details of a specific quote request.
    Restricted to Admins OR the Buyer who created it.
    """
    quote = get_object_or_404(QuoteRequest, id=quote_request_id)
    
    # Security Check: Only allow Admin or the Owner to view
    if not request.user.is_superuser and quote.buyer != request.user:
        messages.error(request, "You do not have permission to view this quote.")
        return redirect('home')

    # FIX HERE: Change the template path to include the app directory
    return render(request, 'payment/quote_request_details.html', {'quote': quote})

    

@login_required
def quote_request_list(request):
    """
    List quote requests.
    - Admins see ALL requests sorted by newest.
    - Regular users see ONLY their own requests.
    """
    if request.user.is_superuser:
        quotes = QuoteRequest.objects.all().order_by('-created_at')
        page_title = "Manage Quote Requests (Admin)"
    else:
        quotes = QuoteRequest.objects.filter(buyer=request.user).order_by('-created_at')
        page_title = "My Quote History"

    return render(request, 'store/quote_request_list.html', {
        'quotes': quotes,
        'page_title': page_title
    })