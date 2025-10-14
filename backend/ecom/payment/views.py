# payment/views.py
"""
Cleaned, consolidated payment/views for Helios.
Drop this file into payment/views.py (backup original first).
"""

from decimal import Decimal
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib import messages as message
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db import transaction
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField

from cart.cart import Cart
from store.models import Product, Profile
from store.forms import ProductForm
from .email_utils import send_order_notifications
from .decorators import seller_required
from .forms import (
    ShippingForm,
    PaymentForm,
    SellerSignupForm,
    SellerLoginForm,
    SellerProfileForm,
)
from .models import ShippingAddress, Order, OrderItem, Seller, Notification

# Optional Impact transaction model (may exist in your models)
try:
    from .models import ImpactFundTransaction
except Exception:
    ImpactFundTransaction = None

User = get_user_model()


# -------------------------
# Notifications views
# -------------------------
@login_required
def notifications_list(request):
    """Full list view of notifications for the logged-in user."""
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'payment/notifications_list.html', {'notifications': notifs})


# payment/views.py (UPDATED notification_open)
# ...

# payment/views.py (SIMPLIFIED notification_open)
# ...

# payment/views.py

@login_required
def notification_open(request, pk):
    """
    Mark notification read and redirect safely:
      - If notification has order_id:
            - If current user is a seller who has items in that order -> seller-facing order view
            - Else if current user is superuser -> admin change page for the order
            - Else if current user is the customer who placed the order -> customer/home or a user order page
            - Otherwise -> notifications list (or home)
    """
    try:
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
    except Exception:
        return HttpResponseForbidden("You cannot access this notification.")

    # mark read (idempotent)
    if not notif.is_read:
        notif.is_read = True
        notif.save(update_fields=['is_read'])

    # If notification links to an order, decide redirect based on role/ownership
    if notif.order_id:
        try:
            order = Order.objects.get(pk=notif.order_id)
        except Order.DoesNotExist:
            message.error(request, "The linked order could not be found.")
            return redirect('notifications_list')

        
        # --- 1. SELLER CHECK (Redirect to Dashboard with Context) ---
        seller_profile = getattr(request.user, 'seller_profile', None)
        if seller_profile is not None:
            
            # Check if the seller has any items in this specific order
            seller_has_items_in_order = OrderItem.objects.filter(
                order=order, 
                seller=seller_profile
            ).exists()

            if seller_has_items_in_order:
                # 👇 SMART COMPROMISE: Redirect to the dashboard (safer navigation)
                # The notification alert link (which is not this view) will still work as before.
                message.info(
                    request, 
                    f"Notification for Order #{order.id}. Find your items listed below."
                )
                # Ensure 'seller_dashboard' is the correct URL name
                return redirect('seller_dashboard') 


        # --- 2. SUPERUSER/ADMIN CHECK ---
        if request.user.is_superuser:
            # Redirect admin to Django Admin change page
            return redirect(reverse('admin:payment_order_change', args=(order.id,)))


        # --- 3. CUSTOMER CHECK ---
        if order.user and request.user == order.user:
            return redirect('home')

        # --- 4. DEFAULT FALLBACK ---
        return redirect('notifications_list')

    # If notification didn't link to an order, send to the notifications list
    return redirect('notifications_list')


@login_required
def notification_redirect_view(request, notif_id):
    """Backward-compatible wrapper — just call notification_open."""
    # The wrapper exists because some templates used this name earlier.
    return notification_open(request, notif_id)



@login_required
def mark_all_notifications_read(request):
    """Mark all unread notifications for the current user as read (POST only)."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=400)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'ok': True})


# -------------------------
# Seller-facing order detail view(s)
# -------------------------
@login_required
def seller_order_detail(request, order_id):
    """
    Seller-facing order detail.
    - Admins see everything.
    - Sellers only see items that belong to them and see calculations for their items.
    """
    order = get_object_or_404(Order, pk=order_id)

    # --- 1. Superuser/Admin Flow ---
    if request.user.is_superuser:
        items = OrderItem.objects.filter(order=order).select_related('product', 'seller')
        seller_view = False
        
        # Calculate full order totals (if you need them for the admin view)
        full_subtotal = sum(item.price * item.quantity for item in items)
        full_commission = sum(item.price * item.quantity * item.commission_rate for item in items)
        
        return render(request, 'payment/seller_order_detail.html', {
            'order': order, 
            'items': items, 
            'seller_view': seller_view,
            'seller_subtotal': full_subtotal.quantize(Decimal('0.01')),
            'total_commission': full_commission.quantize(Decimal('0.01')),
            'seller_net_earnings': (full_subtotal - full_commission).quantize(Decimal('0.01')),
        })

    # --- 2. Seller Authentication Check ---
    if not hasattr(request.user, 'seller_profile') or request.user.seller_profile is None:
        return HttpResponseForbidden("You must be a seller to view this page.")

    seller = request.user.seller_profile
    items = OrderItem.objects.filter(order=order, seller=seller).select_related('product')
    
    if not items.exists():
        return HttpResponseForbidden("You do not have permission to view this order.")

    # --- 3. Seller Calculations ---
    seller_subtotal = Decimal('0.00')
    total_commission = Decimal('0.00')
    
    for item in items:
        # NOTE: commission_rate should be a Decimal field for accurate multiplication
        item_subtotal = item.price * item.quantity
        item_commission = item_subtotal * item.commission_rate
        
        seller_subtotal += item_subtotal
        total_commission += item_commission

    # Final totals (quantized for currency precision)
    seller_subtotal = seller_subtotal.quantize(Decimal('0.01'))
    total_commission = total_commission.quantize(Decimal('0.01'))
    seller_net_earnings = (seller_subtotal - total_commission).quantize(Decimal('0.01'))
    
    # --- 4. Handle POST Request (Status Update) ---
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action in ['processing', 'shipped', 'delivered', 'cancelled']:
            # You might need additional checks here to ensure the seller can only advance certain statuses
            order.status = action
            if action == 'shipped':
                 order.date_shipped = timezone.now()
            order.save()
            message.success(request, f"Order #{order.id} status updated to {action}.")
        else:
            message.error(request, "Invalid status action.")

        # Redirect to prevent re-submission of form
        return redirect('seller_order_detail', order_id=order.id)


    # --- 5. Render Template ---
    seller_view = True
    return render(request, 'payment/seller_order_detail.html', {
        'order': order, 
        'items': items, 
        'seller_view': seller_view,
        'seller_subtotal': seller_subtotal,
        'total_commission': total_commission,
        'seller_net_earnings': seller_net_earnings,
    })


# alias (if some URLs/templates reference the plural name)
seller_order_details = seller_order_detail
# -------------------------
# Seller product CRUD
# -------------------------
@seller_required
def product_list(request):
    seller = request.user.seller_profile
    products = Product.objects.filter(seller=seller).order_by('-id')
    return render(request, 'payment/product_list.html', {'products': products})


@seller_required
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            new_product = form.save(commit=False)
            new_product.seller = request.user.seller_profile
            new_product.save()
            message.success(request, "Product added successfully!")
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'payment/product_form.html', {'form': form, 'action': 'Add'})


@seller_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user.seller_profile)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            message.success(request, "Product updated successfully!")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'payment/product_form.html', {'form': form, 'action': 'Edit', 'product': product})


@seller_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user.seller_profile)
    if request.method == 'POST':
        product.delete()
        message.success(request, f"Product '{product.name}' deleted successfully!")
        return redirect('product_list')
    return render(request, 'payment/product_confirm_delete.html', {'product': product})


# -------------------------
# Seller account lifecycle (signup/login/logout/profile)
# -------------------------
def seller_signup(request):
    if request.method == 'POST':
        form = SellerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Make sure seller_profile exists and is inactive until admin approves
            if hasattr(user, "seller_profile"):
                user.seller_profile.is_active = False
                user.seller_profile.save()
            message.success(request, "Your seller application has been submitted successfully! We'll review it and get back to you shortly.")
            return redirect('home')
    else:
        form = SellerSignupForm()
    return render(request, 'payment/seller_signup.html', {'form': form})


def seller_login(request):
    if request.method == "POST":
        form = SellerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not hasattr(user, 'seller_profile'):
                message.error(request, "Account is not a seller.")
                return redirect('seller_signup')
            login(request, user)
            return redirect('seller_dashboard')
        message.error(request, "Invalid credentials.")
    else:
        form = SellerLoginForm()
    return render(request, 'payment/seller_login.html', {'form': form})


def seller_logout(request):
    logout(request)
    message.success(request, "Logged out.")
    return redirect('home')


@seller_required
def seller_dashboard(request):
    # ... (code remains the same above this line)
    request.disable_newsletter = True
    seller = request.user.seller_profile

    order_items_qs = OrderItem.objects.filter(seller=seller).select_related('order', 'product').order_by('-created_at')

    # ... (filtering logic is unchanged)
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')

    if status_filter != 'all':
        order_items_qs = order_items_qs.filter(order__status=status_filter)

    if search_query:
        order_items_qs = order_items_qs.filter(
            Q(order__full_name__icontains=search_query) |
            Q(order__email__icontains=search_query) |
            Q(order__id__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )
    # ...

    # Get the unique orders IDs and fetch the Orders
    order_ids = order_items_qs.values_list('order_id', flat=True).distinct()
    orders = Order.objects.filter(id__in=order_ids).order_by('-date_ordered')

    seller_items_map = {}
    
    # 👇 NEW DICTIONARY FOR CALCULATIONS 👇
    seller_totals_map = {} 
    
    for item in order_items_qs:
        # Aggregate OrderItems into a list per Order ID
        if item.order_id not in seller_items_map:
            seller_items_map[item.order_id] = []
        seller_items_map[item.order_id].append(item)

        # Aggregate totals per Order ID
        if item.order_id not in seller_totals_map:
            seller_totals_map[item.order_id] = {'subtotal': Decimal('0.00'), 'commission': Decimal('0.00')}
        
        # Calculate subtotal and commission for this specific order item
        item_subtotal = item.price * item.quantity
        item_commission = item_subtotal * item.commission_rate
        
        seller_totals_map[item.order_id]['subtotal'] += item_subtotal
        seller_totals_map[item.order_id]['commission'] += item_commission
        
    # Apply Decimal formatting to the aggregated totals
    for order_id in seller_totals_map:
         seller_totals_map[order_id]['subtotal'] = seller_totals_map[order_id]['subtotal'].quantize(Decimal('0.01'))
         seller_totals_map[order_id]['commission'] = seller_totals_map[order_id]['commission'].quantize(Decimal('0.01'))


    context = {
        'orders': orders,
        'seller_items_map': seller_items_map,
        # 👇 PASS THE NEW MAP TO CONTEXT 👇
        'seller_totals_map': seller_totals_map, 
        'current_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'payment/seller_dashboard.html', context)


@seller_required
def seller_profile_view(request):
    request.disable_newsletter = True
    seller = request.user.seller_profile
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, request.FILES, instance=seller)
        if form.is_valid():
            form.save()
            message.success(request, "Profile updated.")
            return redirect('seller_profile')
    else:
        form = SellerProfileForm(instance=seller)
    return render(request, 'payment/seller_profile.html', {'form': form, 'seller': seller})


# -------------------------
# Admin helpers
# -------------------------
def is_superuser(user):
    return user.is_authenticated and user.is_superuser


@user_passes_test(is_superuser)
def orders(request, pk):
    """Admin view for a single order."""
    order = get_object_or_404(Order, pk=pk)
    items = order.orderitem_set.all()
    total_commission = sum((item.price * item.quantity * item.commission_rate) for item in items)
    return render(request, 'payment/admin_order_details.html', {'order': order, 'items': items, 'total_commission': total_commission})


# -------------------------
# Admin dashboards (unshipped / shipped)
# -------------------------
def not_shipped_dash(request):
    request.disable_newsletter = True
    if not request.user.is_authenticated or not request.user.is_superuser:
        message.warning(request, "Access Denied")
        return redirect('home')

    if request.method == "POST":
        order_id = request.POST.get('num')
        action = request.POST.get('action')
        try:
            order = Order.objects.get(id=order_id)
            if action == 'ship':
                order.status = 'shipped'
                order.date_shipped = timezone.now()
                order.save()
                message.success(request, f"Order #{order_id} marked as shipped")
            elif action == 'cancel':
                cancellation_reason = request.POST.get('reason', 'Cancelled by admin')
                order.status = 'cancelled'
                order.cancellation_notes = cancellation_reason
                order.save()
                message.success(request, f"Order #{order_id} has been cancelled")
        except Order.DoesNotExist:
            message.error(request, "Order not found")

        status_filter = request.GET.get('status', 'active')
        search_query = request.GET.get('search', '')
        redirect_url = f"{reverse('not_shipped_dash')}?status={status_filter}&search={search_query}"
        return redirect(redirect_url)

    status_filter = request.GET.get('status', 'active')
    search_query = request.GET.get('search', '')

    if status_filter == 'cancelled':
        orders_qs = Order.objects.filter(status='cancelled')
    elif status_filter == 'all':
        orders_qs = Order.objects.exclude(status__in=['shipped', 'delivered'])
    else:
        orders_qs = Order.objects.filter(status__in=['paid', 'processing'])

    if search_query:
        orders_qs = orders_qs.filter(full_name__icontains=search_query) | orders_qs.filter(id__icontains=search_query) | orders_qs.filter(email__icontains=search_query)

    orders_qs = orders_qs.select_related('user').order_by('-date_ordered')
    return render(request, 'payment/not_shipped_dash.html', {"orders": orders_qs, "current_filter": status_filter, "search_query": search_query})


def shipped_dash(request):
    request.disable_newsletter = True
    if not request.user.is_authenticated or not request.user.is_superuser:
        message.warning(request, "Access Denied")
        return redirect('home')

    if request.method == "POST":
        order_id = request.POST.get('num')
        action = request.POST.get('action')
        try:
            order = Order.objects.get(id=order_id)
            if action == 'deliver':
                order.status = 'delivered'
                order.save()
                message.success(request, f"Order #{order_id} marked as delivered")
            elif action == 'process':
                order.status = 'processing'
                order.save()
                message.success(request, f"Order #{order_id} returned to processing")
        except Order.DoesNotExist:
            message.error(request, "Order not found")

        status_filter = request.GET.get('status', 'all')
        search_query = request.GET.get('search', '')
        redirect_url = f"{reverse('shipped_dash')}?status={status_filter}&search={search_query}"
        return redirect(redirect_url)

    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')

    if status_filter == 'delivered':
        orders_qs = Order.objects.filter(status='delivered')
    elif status_filter == 'shipped':
        orders_qs = Order.objects.filter(status='shipped')
    else:
        orders_qs = Order.objects.filter(status__in=['shipped', 'delivered'])

    if search_query:
        orders_qs = orders_qs.filter(full_name__icontains=search_query) | orders_qs.filter(id__icontains=search_query) | orders_qs.filter(email__icontains=search_query)

    orders_qs = orders_qs.select_related('user').order_by('-date_shipped')
    return render(request, 'payment/shipped_dash.html', {"orders": orders_qs, "current_filter": status_filter, "search_query": search_query})


# -------------------------
# Order processing (checkout)
# -------------------------
def process_order(request):
    """
    Full checkout/order creation logic.
    Creates Order, OrderItems, ImpactFundTransaction (best-effort), notifications and clears cart.
    """
    request.disable_newsletter = True
    if request.method != "POST":
        message.success(request, "Access Denied")
        return redirect('home')

    cart = Cart(request)
    cart_products = cart.get_prods()
    quantities = cart.get_quants()
    total = cart.cart_total()
    my_shipping = request.session.get('my_shipping') or {}

    full_name = my_shipping.get('shipping_full_name', '')
    email = my_shipping.get('shipping_email', '')
    phone_number = my_shipping.get('phone_number', '') 
    shipping_address = (
        f"{my_shipping.get('shipping_address1','')}\n"
        f"{my_shipping.get('shipping_address2','')}\n"
        f"{my_shipping.get('shipping_city','')}\n"
        f"{my_shipping.get('shipping_province','')}\n"
        f"{my_shipping.get('shipping_postal_code','')}\n"
        f"{my_shipping.get('shipping_country','')}"
    )
    amount_paid = Decimal(total) if not isinstance(total, Decimal) else total
    payment_method = request.POST.get('payment_method', None)

    ITEM_COMMISSION_RATE = Decimal('0.15')
    IMPACT_FUND_RATE = Decimal('0.10')

    total_impact_allocation = Decimal('0.00')

    with transaction.atomic():
        # Create order (auth or guest)
        if request.user.is_authenticated:
            order = Order(user=request.user, full_name=full_name, email=email, 
                          shipping_address=shipping_address, amount_paid=amount_paid, phone_number=phone_number,
                            
                          status='paid', payment_method=payment_method)
        else:
            order = Order(full_name=full_name, email=email,
                          shipping_address=shipping_address, amount_paid=amount_paid, phone_number=phone_number,
                          
                          status='paid', payment_method=payment_method)
        order.save()

        order_items = []
        user_for_impact = request.user if request.user.is_authenticated else None

        for product in cart_products:
            product_id = product.id
            price = product.sale_price if getattr(product, 'is_sale', False) and getattr(product, 'sale_price', None) else product.price
            if not isinstance(price, Decimal):
                price = Decimal(price)

            for key, value in quantities.items():
                try:
                    q_key = int(key)
                except (ValueError, TypeError):
                    continue
                if q_key != product_id:
                    continue

                quantity = int(value)
                oi = OrderItem(order=order, product=product, user=user_for_impact,
                               quantity=quantity, price=price, commission_rate=ITEM_COMMISSION_RATE)
                oi.save()
                order_items.append(oi)

                item_subtotal = (price * Decimal(quantity)).quantize(Decimal('0.01'))
                platform_commission = (item_subtotal * ITEM_COMMISSION_RATE).quantize(Decimal('0.01'))
                impact_allocation = (platform_commission * IMPACT_FUND_RATE).quantize(Decimal('0.01'))
                total_impact_allocation += impact_allocation

        # Create ImpactFundTransaction if model exists
        if total_impact_allocation > Decimal('0.00') and ImpactFundTransaction is not None:
            try:
                ImpactFundTransaction.objects.create(
                    transaction_type='COMMISSION',
                    amount=total_impact_allocation,
                    user=user_for_impact,
                    description=f"Impact allocation from Order #{order.pk} ({(IMPACT_FUND_RATE * 100)}% of commission)",
                )
            except Exception as e:
                print("ImpactFundTransaction create failed:", e)

        # Send notifications (best-effort)
        print("DEBUG 1: Before calling send_order_notifications. Order items count:", len(order_items))
        try:
            send_order_notifications(order, order_items)
            print("DEBUG 2: send_order_notifications called successfully.")
        except Exception as e:
            print("Error sending notifications:", e)

        # Clear cart
        try:
            if hasattr(cart, "clear"):
                cart.clear()
            else:
                for key in list(request.session.keys()):
                    if key == "session_key":
                        del request.session[key]
        except Exception:
            pass

    message.success(request, "Order Placed Successfully")
    return redirect('home')


# -------------------------
# Billing/Checkout helpers + exports
# -------------------------
def billing_info(request):
    request.disable_newsletter = True
    
    # Check if shipping data exists in the session
    my_shipping = request.session.get('my_shipping')
    if not my_shipping:
        # If shipping data is missing, redirect back to checkout
        message.warning(request, "Please enter your shipping information.")
        return redirect('checkout')

    # Now the view is guaranteed to have clean shipping data
    cart = Cart(request)
    cart_products = cart.get_prods()
    quantities = cart.get_quants()
    total = cart.cart_total()

    billing_form = PaymentForm() 
    return render(request, 'payment/billing_info.html', {
        "cart_products": cart_products,
        "quantities": quantities,
        "total": total,
        "shipping_info": my_shipping, # Use the clean session data
        "billing_form": billing_form
    })


def checkout(request):
    # ... (code to get cart, products, etc.) ...

    if request.user.is_authenticated:
        shipping_user, created = ShippingAddress.objects.get_or_create(user=request.user)
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
    else:
        shipping_form = ShippingForm(request.POST or None)

    # --- MUST BE PRESENT: Form Validation and Session Save ---
    if request.method == 'POST':
        if shipping_form.is_valid():
            request.session['my_shipping'] = shipping_form.cleaned_data
            
            if request.user.is_authenticated:
                shipping_form.save()
            
            # SUCCESS! Redirect to the next step
            return redirect('billing_info') 
        else:
            # Form invalid, errors will show on the rendered page
            message.error(request, "Please correct the errors in your shipping information.")
            # FALL THROUGH to render the page with errors
    # --------------------------------------------------------

    return render(request, 'payment/checkout.html', {
        # ... (context data) ...
        "shipping_form": shipping_form
    })


def payment_success(request):
    return render(request, 'payment/payment_success.html', {})


@login_required
def export_order_details(request, order_id):
    """
    Exports order details as a text file.
    - Allowed for Superusers (any order).
    - Allowed for Sellers (only orders that contain their products).
    """
    order = get_object_or_404(Order, id=order_id)
    
    # --- 1. Permission Check ---
    is_seller = hasattr(request.user, 'seller_profile') and request.user.seller_profile is not None
    allowed = False
    
    if request.user.is_superuser:
        allowed = True
    elif is_seller:
        # Check if the order contains any OrderItem sold by this seller
        allowed = OrderItem.objects.filter(
            order=order, 
            seller=request.user.seller_profile
        ).exists()

    if not allowed:
        if order.user == request.user:
            # If the customer wants their own order details, they should probably be redirected 
            # to a customer order history view, but for export simplicity, we deny for now.
            pass 
        return HttpResponse("Access Denied. You are not authorized to export details for this order.", status=403)

    # --- 2. Data Retrieval and Calculation ---
    
    # Only retrieve items relevant to the seller if the user is a seller and not a superuser
    if is_seller and not request.user.is_superuser:
        items = OrderItem.objects.filter(order=order, seller=request.user.seller_profile).select_related('product')
    else:
        # Superuser gets all items
        items = OrderItem.objects.filter(order=order).select_related('product')
    
    # Recalculate totals based on the filtered items queryset
    total_subtotal_seller_view = Decimal('0.00')
    total_commission_seller_view = Decimal('0.00')
    
    for item in items:
        # Ensure price is a Decimal for math
        price = item.price if isinstance(item.price, Decimal) else Decimal(str(item.price))
        
        item_subtotal = price * item.quantity
        item_commission = item_subtotal * item.commission_rate
        total_subtotal_seller_view += item_subtotal
        total_commission_seller_view += item_commission
        
        # Attach the calculated commission amount to the item object for use in the loop below
        item.calculated_commission_amount = item_commission.quantize(Decimal('0.01'))
        item.calculated_subtotal = item_subtotal.quantize(Decimal('0.01'))


    # --- 3. Content Generation ---
    content = f"""ORDER #{order.id}
===========
Customer: {order.full_name}
Email: {order.email}
Phone Number: {order.phone_number}
Amount Paid (Order Total): ZMK {order.amount_paid}
Status: {order.get_status_display()}
Payment Method: {order.get_payment_method_display()}

Shipping Address:
{order.shipping_address}

Items {'(Your Products Only)' if is_seller and not request.user.is_superuser else '(Full Order)'}:
-------------"""
    
    for item in items:
        content += f"\n- {item.product.name}"
        content += f"\n  Quantity: {item.quantity} @ ZMK {item.price} each"
        content += f"\n  Subtotal: ZMK {item.calculated_subtotal}"
        content += f"\n  Commission ({item.commission_rate * 100}%): ZMK {item.calculated_commission_amount}"

    # Use the logged-in user's username for the summary heading
    content += f"\n\nSeller Summary ({request.user.username}'s Items):"
    content += f"\n-------------"
    content += f"\nTotal Subtotal (Your items): ZMK {total_subtotal_seller_view.quantize(Decimal('0.01'))}"
    content += f"\nTotal Commission (Your items): ZMK {total_commission_seller_view.quantize(Decimal('0.01'))}"
    content += f"\nNet Earnings: ZMK {(total_subtotal_seller_view - total_commission_seller_view).quantize(Decimal('0.01'))}"

    # --- 4. HTTP Response ---
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="order_{order_id}_details.txt"'
    return response


# -------------------------
# Utilities: update_order_status (used by seller/admin pages)
# -------------------------
def cancel_order(request, order_id):
    if request.method == "POST":
        # Check seller permissions here if necessary
        
        order = get_object_or_404(Order, id=order_id)
        
        # --- ADD YOUR CANCELLATION LOGIC HERE ---
        try:
            # 1. Update the order status
            order.status = 'cancelled'
            order.cancellation_notes = "Cancelled by seller." # Add seller notes if needed
            order.save()
            
            # 2. Add logic to refund the customer or handle payment status
            # 3. Add logic to notify the customer/admin
            
            message.success(request, f"Order #{order_id} has been successfully cancelled.")
        except Exception as e:
            message.error(request, f"Failed to cancel order #{order_id}. Error: {e}")
            
    # Redirect back to the order detail page or seller dashboard
    return redirect('seller_order_detail', order_id=order_id)


@seller_required
def update_order_status(request, pk):
    """
    POST-only endpoint to update order status.
    Sellers may only update orders that contain their products.
    Admins may update any order.
    """
    if request.method != 'POST':
        message.warning(request, "Invalid request.")
        return redirect('seller_dashboard')

    order = get_object_or_404(Order, pk=pk)

    # --- 1. Permission Check ---
    if request.user.is_superuser:
        allowed = True
    else:
        seller_profile = getattr(request.user, 'seller_profile', None)
        if not seller_profile:
            message.error(request, "Access denied. You must be a seller.")
            return redirect('seller_dashboard')
        # Check if the order contains any OrderItem sold by this seller
        allowed = OrderItem.objects.filter(order=order, seller=seller_profile).exists()

    if not allowed:
        message.error(request, "Access denied. You can only update orders that contain your products.")
        # Redirect back to the order detail page for the forbidden action
        return redirect('seller_order_detail', order_id=order.id)

    # --- 2. Process Action ---
    action = (request.POST.get('action') or '').strip().lower()
    updated = False

    if action == 'processing' and order.status in ['paid', 'pending']:
        order.status = 'processing'
        updated = True
        message.success(request, f"Order #{order.id} set to Processing.")
    
    elif action == 'shipped' and order.status == 'processing':
        order.status = 'shipped'
        order.date_shipped = timezone.now() # Record ship date
        updated = True
        message.success(request, f"Order #{order.id} marked as Shipped.")
    
    elif action == 'delivered' and order.status == 'shipped':
        order.status = 'delivered'
        updated = True
        message.success(request, f"Order #{order.id} marked as Delivered.")
    
    # Allow cancellation from any status that isn't already final (delivered/cancelled)
    elif action == 'cancelled' and order.status not in ['delivered', 'cancelled']:
        order.status = 'cancelled'
        updated = True
        message.success(request, f"Order #{order.id} Cancelled.")
    
    else:
        message.warning(request, "Invalid or disallowed status transition.")

    if updated:
        # NOTE: Using save() directly instead of the assumed order.update_status() method
        order.save() 
        
        # --- 3. Create Admin Notification ---
        try:
            # Assuming User and Notification are correctly imported
            admin_email = getattr(settings, 'ADMIN_EMAIL', None)
            admin_user = None
            if admin_email:
                # Find admin user by email
                admin_user = User.objects.filter(email=admin_email, is_superuser=True).first()
            if admin_user:
                Notification.objects.create(
                    user=admin_user,
                    message=f"Order #{order.id} status changed to {order.get_status_display()} by {request.user.username}",
                    order_id=order.id
                )
        except Exception as e:
            # Log the exception instead of just passing
            print(f"Error creating admin notification: {e}") 


    # --- 4. Redirect to Order Detail View (Crucial for the new UI flow) ---
    return redirect('seller_order_detail', order_id=order.id)
