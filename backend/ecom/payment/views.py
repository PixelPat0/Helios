from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages as message
from django.utils import timezone
from django.db.models import Q
from cart.cart import Cart
from .forms import ShippingForm, PaymentForm, SellerSignupForm, SellerLoginForm, SellerProfileForm
from .models import ShippingAddress, Order, OrderItem, Seller
from store.models import Product, Profile, Product
from django.contrib.auth.models import User
import datetime
from decimal import Decimal
from .email_utils import send_order_notifications
from django.urls import reverse
from django.contrib.auth import login, logout
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from .decorators import seller_required
# form imports for the seller views
from .forms import SellerSignupForm, SellerLoginForm, SellerProfileForm
# Product forms for the seller views
from store.forms import ProductForm
from django.contrib.auth.decorators import user_passes_test


@seller_required
def update_order_status(request, pk):
    """
    Handles POST requests to update the status of a specific order.
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        seller = request.user.seller_profile
        
        # Check if the order contains at least one product from the current seller
        if not OrderItem.objects.filter(order=order, product__seller=seller).exists():
            message.error(request, "Access denied. You can only update the status of orders that contain your products.")
            return redirect('seller_dashboard')
            
        action = request.POST.get('action')
        
        if action == 'processing' and order.status == 'paid':
            order.status = 'processing'
            order.save()
            message.success(request, f"Order {order.id} is now being processed.")
            
        elif action == 'shipped' and order.status == 'processing':
            order.status = 'shipped'
            order.save()
            message.success(request, f"Order {order.id} has been marked as shipped.")
            
        elif action == 'delivered' and order.status == 'shipped':
            order.status = 'delivered'
            order.save()
            message.success(request, f"Order {order.id} has been marked as delivered.")

    return redirect('seller_dashboard')


@seller_required
def seller_order_details(request, pk):
    """
    Displays the details of a specific order for the logged-in seller.
    It verifies that the order contains at least one item from the seller.
    """
    seller = request.user.seller_profile
    
    # Get the order and its items, ensuring at least one item belongs to the seller
    order = get_object_or_404(Order, pk=pk)
    
    # Filter order items to only include those belonging to the current seller
    seller_order_items = OrderItem.objects.filter(order=order, product__seller=seller)
    
    # If the seller has no items in this order, deny access
    if not seller_order_items.exists():
        message.error(request, "Access denied. This order does not contain your products.")
        return redirect('seller_dashboard')

    # Calculate subtotal and total commission for the seller's items in this order
    subtotal = seller_order_items.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or 0

    total_commission = seller_order_items.aggregate(
        commission_sum=Sum(
            ExpressionWrapper(
                F('price') * F('quantity') * F('commission_rate'),
                output_field=DecimalField()
            )
        )
    )['commission_sum'] or 0
    
    net_profit = subtotal - total_commission

    context = {
        'order': order,
        'seller_order_items': seller_order_items,
        'subtotal': subtotal,
        'total_commission': total_commission,
        'net_profit': net_profit,
    }
    
    return render(request, 'payment/seller_order_details.html', context)


@seller_required
def product_list(request):
    """
    Displays a list of all products belonging to the current seller.
    """
    seller = request.user.seller_profile
    products = Product.objects.filter(seller=seller).order_by('-id')
    
    context = {
        'products': products
    }
    return render(request, 'payment/product_list.html', context)

@seller_required
def product_add(request):
    """
    Allows a seller to add a new product.
    """
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
    
    context = {
        'form': form,
        'action': 'Add'
    }
    return render(request, 'payment/product_form.html', context)

@seller_required
def product_edit(request, pk):
    """
    Allows a seller to edit one of their products.
    Includes a security check to ensure they own the product.
    """
    product = get_object_or_404(Product, pk=pk, seller=request.user.seller_profile)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            message.success(request, "Product updated successfully!")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'action': 'Edit',
        'product': product
    }
    return render(request, 'payment/product_form.html', context)

@seller_required
def product_delete(request, pk):
    """
    Handles the deletion of a product.
    Includes a security check to ensure the seller owns the product.
    """
    product = get_object_or_404(Product, pk=pk, seller=request.user.seller_profile)
    
    if request.method == 'POST':
        product.delete()
        message.success(request, f"Product '{product.name}' deleted successfully!")
        return redirect('product_list')
    
    context = {
        'product': product
    }
    return render(request, 'payment/product_confirm_delete.html', context)

#Seller lifecycle (signup, login, logout, profile)


def seller_signup(request): 
    if request.method == 'POST':
        form = SellerSignupForm(request.POST)
        if form.is_valid():
            # The save method in the form handles creating the User and Seller
            user = form.save() 



            # We are making sure that the related Seler profile is inactive until approved by admin
            #This should be working now
            if hasattr(user, "seller_profile"):
                user.seller_profile.is_active = False
                user.seller_profile.save()
                
            message.success(request, "Your seller application has been submitted successfully! We'll review it and get back to you shortly.")
            return redirect('home')  # Redirect to the home page after submission
    else:
        form = SellerSignupForm()
    
    context = {'form': form}
    return render(request, 'payment/seller_signup.html', context)

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
    # Fetch all order items for the logged-in seller
    seller_id = request.user.seller_profile.id
    order_items = OrderItem.objects.filter(seller__id=seller_id).select_related('order').order_by('-created_at')

    # Get filter and search parameters from the request
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')

    # Apply filters
    if status_filter != 'all':
        order_items = order_items.filter(order__status=status_filter)
    
    if search_query:
        order_items = order_items.filter(
            Q(order__full_name__icontains=search_query) |
            Q(order__email__icontains=search_query) |
            Q(order__id__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )

    # To show unique orders, not unique order items
    # You might want to display individual items, but if you want one row per order,
    # you'd group them. For simplicity, let's stick to OrderItems first.
    # To display unique orders, you could do:
    order_ids = order_items.values_list('order_id', flat=True).distinct()
    orders = Order.objects.filter(id__in=order_ids).order_by('-date_ordered')

    # We will pass both order_items (for detail view) and orders (for the main table)
    # Let's adjust for the request of "all on one page but with the help of filters"
    
    # We will just show all order items in a table, and the filter will apply to the order status
    context = {
        'orders': orders, # This will be the list of orders to display
        'current_filter': status_filter,
        'search_query': search_query,
    }

    return render(request, 'payment/seller_dashboard.html', context)

    
@seller_required
def seller_profile_view(request):
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

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_superuser)
def orders(request, pk):
    """
    Displays the details of a specific order for the admin.
    """
    order = get_object_or_404(Order, pk=pk)
    
    # You might want to get all order items, not just a subset
    items = order.orderitem_set.all()
    
    # For a full admin view, you might not need to calculate commission,
    # but let's include it for consistency with the seller dashboard.
    total_commission = 0
    for item in items:
        total_commission += item.price * item.quantity * item.commission_rate
        
    context = {
        'order': order,
        'items': items, # Changed from orderitem_set to items for clarity
        'total_commission': total_commission,
    }
    
    return render(request, 'payment/admin_order_details.html', context)

# payments/views.py

def not_shipped_dash(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        message.warning(request, "Access Denied")
        return redirect('home')
    
    # Handle POST requests (button actions)
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
                reason = request.POST.get('reason', 'No reason provided')
                order.status = 'cancelled'
                # If you have a cancellation_notes field, add it here
                # order.cancellation_notes = reason
                order.save()
                message.success(request, f"Order #{order_id} has been cancelled")
                
        except Order.DoesNotExist:
            message.error(request, "Order not found")
        
        # Redirect back to the same page with current filters
        status_filter = request.GET.get('status', 'active')
        search_query = request.GET.get('search', '')
        redirect_url = f"{reverse('not_shipped_dash')}?status={status_filter}&search={search_query}"
        return redirect(redirect_url)
    
    # Get filter parameters from URL (GET request handling remains the same)
    status_filter = request.GET.get('status', 'active')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    if status_filter == 'cancelled':
        orders = Order.objects.filter(status='cancelled')
    elif status_filter == 'all':
        orders = Order.objects.exclude(status__in=['shipped', 'delivered'])
    else:  # active orders
        orders = Order.objects.filter(status__in=['paid', 'processing'])
    
    # Apply search if provided
    if search_query:
        orders = orders.filter(
            full_name__icontains=search_query
        ) | orders.filter(
            id__icontains=search_query
        ) | orders.filter(
            email__icontains=search_query
        )
    
    # Final ordering
    orders = orders.select_related('user').order_by('-date_ordered')
    
    return render(request, 'payment/not_shipped_dash.html', {
        "orders": orders,
        "current_filter": status_filter,
        "search_query": search_query
    })

def shipped_dash(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        message.warning(request, "Access Denied")
        return redirect('home')
    
    # Handle POST requests (button actions)
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
        
        # Redirect back to the same page with current filters
        status_filter = request.GET.get('status', 'all')
        search_query = request.GET.get('search', '')
        redirect_url = f"{reverse('shipped_dash')}?status={status_filter}&search={search_query}"
        return redirect(redirect_url)
    
    # Get filter parameters (GET request handling remains the same)
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    if status_filter == 'delivered':
        orders = Order.objects.filter(status='delivered')
    elif status_filter == 'shipped':
        orders = Order.objects.filter(status='shipped')
    else:  # all shipped/delivered orders
        orders = Order.objects.filter(status__in=['shipped', 'delivered'])
    
    # Apply search if provided
    if search_query:
        orders = orders.filter(
            full_name__icontains=search_query
        ) | orders.filter(
            id__icontains=search_query
        ) | orders.filter(
            email__icontains=search_query
        )
    
    # Final ordering
    orders = orders.select_related('user').order_by('-date_shipped')
    
    return render(request, 'payment/shipped_dash.html', {
        "orders": orders,
        "current_filter": status_filter,
        "search_query": search_query
    })


# the meat and potatoes of order processing
def process_order(request):
    if request.method == "POST":
        cart = Cart(request)
        cart_products = cart.get_prods()
        quantities = cart.get_quants()
        total = cart.cart_total()

        payment_form = PaymentForm(request.POST or None)
        # Get Shipping Session Data
        my_shipping = request.session.get('my_shipping')

        # gather order information
        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']
        # Create Shipping Address from session info
        shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_address2']}\n{my_shipping['shipping_city']}\n{my_shipping['shipping_province']}\n{my_shipping['shipping_postal_code']}\n{my_shipping['shipping_country']}"
        amount_paid = total

        # Get payment method
        payment_method = request.POST.get('payment_method')

        # Create Order
        if request.user.is_authenticated:
            create_order = Order(
                user=request.user,
                full_name=full_name,
                email=email,
                shipping_address=shipping_address,
                amount_paid=amount_paid,
                status='paid',
                payment_method=payment_method
            )
            create_order.save()

            # Add Order Items
            order_id = create_order.pk
            order_items = []  # To store items for email notification
            
            for product in cart_products:
                product_id = product.id
                # Get product price
                if product.sale_price:
                    price = product.sale_price
                else:
                    price = product.price

                # Get product quantity
                for key, value in quantities.items():
                    if int(key) == product_id:
                        # create order item
                        create_order_item = OrderItem(
                            order_id=order_id,
                            product=product,
                            user=request.user,
                            quantity=value,
                            price=price,
                            commission_rate=Decimal('0.15')
                        )
                        create_order_item.save()
                        order_items.append(create_order_item)

            # Send email notifications
            try:
                send_order_notifications(create_order, order_items)
            except Exception as e:
                print(f"Error sending notifications: {e}")

            # Delete cart and redirect
            for key in list(request.session.keys()):
                if key == "session_key":
                    del request.session[key]

            message.success(request, "Order Placed Successfully")
            return redirect('home')
        else:
            # Guest checkout
            create_order = Order(
                full_name=full_name,
                email=email,
                shipping_address=shipping_address,
                amount_paid=amount_paid,
                status='paid',
                payment_method=payment_method
            )
            create_order.save()

            order_id = create_order.pk
            order_items = []  # To store items for email notification
            
            for product in cart_products:
                product_id = product.id
                # Get product price
                if product.sale_price:
                    price = product.sale_price
                else:
                    price = product.price

                # Get product quantity
                for key, value in quantities.items():
                    if int(key) == product_id:
                        # create order item
                        create_order_item = OrderItem(
                            order_id=order_id,
                            product=product,
                            quantity=value,
                            price=price,
                            commission_rate=Decimal('0.15')
                        )
                        create_order_item.save()
                        order_items.append(create_order_item)

            # Send email notifications
            try:
                send_order_notifications(create_order, order_items)
            except Exception as e:
                print(f"Error sending notifications: {e}")

            # Delete cart
            for key in list(request.session.keys()):
                if key == "session_key":
                    del request.session[key]

            message.success(request, "Order Placed Successfully")
            return redirect('home')
    else:
        message.success(request, "Access Denied")
        return redirect('home')




def billing_info(request):
    if request.POST:
        cart = Cart(request)
        cart_products = cart.get_prods()
        quantities = cart.get_quants()
        total = cart.cart_total()

        # Store shipping info in session
        if 'shipping_full_name' in request.POST:
            request.session['my_shipping'] = request.POST.dict()
            
        # Get payment form
        billing_form = PaymentForm()
        
        return render(request, 'payment/billing_info.html', {
            "cart_products": cart_products,
            "quantities": quantities,
            "total": total,
            "shipping_info": request.session.get('my_shipping'),
            "billing_form": billing_form
        })
    else:
        message.warning(request, "Access Denied")
        return redirect('home')





def checkout(request):
    cart = Cart(request)
    cart_products = cart.get_prods()
    quantities = cart.get_quants()
    total = cart.cart_total()

    if request.user.is_authenticated:
        #Checkout as logged in user
        #Shipping User
        shipping_user, created = ShippingAddress.objects.get_or_create(user=request.user)
        #Shipping Form
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
        return render(request, 'payment/checkout.html', {
        "cart_products": cart_products,
        "quantities": quantities,
        "total": total,
        "shipping_form": shipping_form
    })

    else:
        #Checkout as guest
        shipping_form = ShippingForm(request.POST or None)
        return render(request, 'payment/checkout.html', {
        "cart_products": cart_products,
        "quantities": quantities,
        "total": total,
        "shipping_form": shipping_form
    })


def payment_success(request):

    return render(request, 'payment/payment_success.html', {})

def export_order_details(request, order_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponse("Access Denied", status=403)
        
    try:
        order = Order.objects.get(id=order_id)
        items = OrderItem.objects.filter(order=order)
        
        # Calculate total commission
        total_commission = sum(item.commission_amount for item in items)
        
        content = f"""ORDER #{order.id}
===========

Customer: {order.full_name}
Email: {order.email}
Amount Paid: ZMK {order.amount_paid}
Status: {order.get_status_display()}
Payment Method: {order.get_payment_method_display()}

Shipping Address:
{order.shipping_address}

Items Ordered:
-------------"""
        
        for item in items:
            content += f"\n- {item.product.name}"
            content += f"\n  Quantity: {item.quantity} @ ZMK {item.price} each"
            content += f"\n  Subtotal: ZMK {item.price * item.quantity}"
            content += f"\n  Commission (15%): ZMK {item.commission_amount}"
            
        content += f"\n\nOrder Summary:"
        content += f"\n-------------"
        content += f"\nSubtotal: ZMK {order.amount_paid}"
        content += f"\nTotal Commission (15%): ZMK {total_commission}"
        content += f"\nNet Amount: ZMK {order.amount_paid - total_commission}"
        
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="order_{order_id}_details.txt"'
        return response
        
    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)

