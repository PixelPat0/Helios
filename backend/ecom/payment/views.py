from django.shortcuts import render, redirect
from cart.cart import Cart

from payment.forms import ShippingForm, PaymentForm
from payment.models import ShippingAddress, Order, OrderItem
from django.contrib.auth.models import User
from django.contrib import messages as message
from store.models import Product


def not_shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=False).order_by('date_ordered')
        return render(request, 'payment/not_shipped_dash.html', {"orders": orders})
    else:    
        message.success(request, "Order Placed Successfully")
        return redirect('home')

def shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=True).order_by('date_ordered')
        return render(request, 'payment/shipped_dash.html', {"orders": orders})
    else:
        message.success(request, "Access Denied")
        return redirect('home')



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


        # Create Order
        if request.user.is_authenticated:

            user = request.user
            create_order = Order(user = user, full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid  )
            create_order.save()

            #Add Order Items
            # Get the order ID
            order_id = create_order.pk
            #get product info
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
                        create_order_item = OrderItem(order_id=order_id, product=product, user=user, quantity=value, price=price)
                        create_order_item.save()

            #delete our cart
            for key in list(request.session.keys()):
                 if key == "session_key":
                      #delete the key
                    del request.session[key]

            message.success(request, "Order Placed Successfully")
            return redirect('home')
        else:
            # If the user is not logged in
            create_order = Order(full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid  )
            create_order.save()

            order_id = create_order.pk
            #get product info
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
                        create_order_item = OrderItem(order_id=order_id, product=product, quantity=value, price=price)
                        create_order_item.save()

            #delete our cart
            for key in list(request.session.keys()):
                 if key == "session_key":
                      #delete the key
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

        # Create a session with Shiping information
        my_shipping= request.POST
        request.session['my_shipping'] = my_shipping

        # Check if the user is logged in
        if request.user.is_authenticated:
            #get the billing form
            billing_form = PaymentForm()
            return render(request, 'payment/billing_info.html', {
            "cart_products": cart_products,
            "quantities": quantities,
            "total": total,
            "shipping_info": request.POST,
            "billing_form": billing_form
    })
        else:
            #not logged in
            billing_form = PaymentForm()
            return render(request, 'payment/billing_info.html', {
            "cart_products": cart_products,
            "quantities": quantities,
            "total": total,
            "shipping_info": request.POST,
            "billing_form": billing_form
    })
   


        shipping_form = request.POST
        return render(request, 'payment/billing_info.html', {
        "cart_products": cart_products,
        "quantities": quantities,
        "total": total,
        "shipping_form": shipping_form
    })
    else:
        message.success(request, "Access Denied")
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

