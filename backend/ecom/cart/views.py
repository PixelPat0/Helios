from django.shortcuts import render, get_object_or_404
from .cart import Cart
from store.models import Product
from django.http import JsonResponse

# Create your views here.


def cart_summary(request):
    #get the cart
    cart = Cart(request)
    #get the products
    cart_products = cart.get_prods()
    quantities = cart.get_quants()
    total = cart.cart_total()
    return render(request, 'cart_summary.html', {"cart_products": cart_products, "quantities":quantities, "total":total})



def cart_add(request):
    cart = Cart(request)
    # Test for POST request
    if request.POST.get('action') == 'post':
        # Extract product_id from POST data
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))
        # Look up the product in the database
        product = get_object_or_404(Product, id=product_id)
        # Add the product to the cart
        cart.add(product=product, quantity=product_qty)
        # Debugging: Print the product and cart session
        print("Product added to cart:", product.name)
        print("Cart session:", cart.cart)
        # Get Cart Count
        cart_quantity = cart.__len__()
        # Return a JSON response
        response = JsonResponse({'qty': cart_quantity})
        return response
    else:
        # If it's not a POST request, return an error
        return JsonResponse({'Error': 'Invalid request'}, status=400)

def cart_delete(request):
    cart = Cart(request)
    # Test for POST request
    if request.POST.get('action') == 'post':
        # Extract product_id from POST data
        product_id = int(request.POST.get('product_id'))
        # call delete function in Cart
        cart.delete(product=product_id)
        response = JsonResponse({'product': product_id})
        return response
    

def cart_update(request):
    cart = Cart(request)
    # Debugging: Print the current cart session
    print("Current cart session before update:", cart.cart)

    # Test for POST request
    if request.POST.get('action') == 'post':
        # Extract product_id from POST data
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))

        # Debugging: Print the received product_id and product_qty
        print("Received product_id:", product_id)
        print("Received product_qty:", product_qty)

        # Update the cart
        cart.update(product=product_id, quantity=product_qty)

        # Debugging: Print the updated cart session
        print("Updated cart session:", cart.cart)

        # Return a JSON response
        response = JsonResponse({'qty': product_qty})
        return response
    else:
        # If it's not a POST request, return an error
        return JsonResponse({'error': 'Invalid request'}, status=400)