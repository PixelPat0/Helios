from django.shortcuts import render, get_object_or_404
from .cart import Cart
from store.models import Product
from django.http import JsonResponse

# Create your views here.


def cart_summary(request):
    return render(request, 'cart_summary.html', {})



def cart_add(request):
    cart = Cart(request)
    # Test for POST request
    if request.POST.get('action') == 'post':
        # Extract product_id from POST data
        product_id = int(request.POST.get('product_id'))
        # Look up the product in the database
        product = get_object_or_404(Product, id=product_id)
        # Add the product to the cart
        cart.add(product=product)
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
    pass

def cart_update(request):
    pass