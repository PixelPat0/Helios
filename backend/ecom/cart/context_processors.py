from .cart import Cart

# create a context processor so our cart can work on all pages

def cart(request):
    # Return the default data from our cart, including items and total price
    return {'cart': Cart(request)}