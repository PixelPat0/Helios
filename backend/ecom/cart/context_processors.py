from .cart import Cart

# create a context processor so our cart can work on all pages

def cart(request):
    """Make cart and cart quantity available in all templates."""
    cart_obj = Cart(request)
    
    # Calculate total quantity
    cart_quantity = cart_obj.__len__()
    
    return {
        'cart': cart_obj,  # The full cart object
        'cart_quantity': cart_quantity,  # Just the quantity count
        'cart_total': cart_obj.cart_total()  # If you need total price too
    }