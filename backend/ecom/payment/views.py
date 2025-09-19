from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages as message
from django.utils import timezone  # Add this import
from cart.cart import Cart
from .forms import ShippingForm, PaymentForm
from .models import ShippingAddress, Order, OrderItem
from store.models import Product, Profile
from django.contrib.auth.models import User
import datetime 
from decimal import Decimal
from .email_utils import send_order_notifications
from django.urls import reverse


def orders(request, pk):
    if request.user.is_authenticated and request.user.is_superuser:
        order = Order.objects.get(id=pk)
        items = OrderItem.objects.filter(order=pk)
        
        if request.method == "POST":
            status = request.POST.get('shipping_status')
            if status == 'true':
                order.update_status('shipped')
                message.success(request, "Order marked as shipped successfully")
            else:
                order.update_status('processing')
                message.success(request, "Order returned to processing")
            return redirect('orders', pk=pk)
        return render(request, 'payment/orders.html', {"order": order, "items": items})
    else:
        message.warning(request, "Access Denied")
        return redirect('home')

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

