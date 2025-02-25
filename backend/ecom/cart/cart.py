class Cart():
    def __init__(self, request):
        self.session = request.session
        # get the current session key if it exists
        cart = self.session.get('session_key')
        # if there is no session key, create one
        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}
        # Make sure cart is available on all pages of site.
        self.cart = cart

    def add(self, product):
        product_id = str(product.id)
        #logic
        if product_id not in self.cart:
            self.cart[product_id] = {'price': str(product.price)}
            self.session.modified = True
            print("Product added to cart:", product_id) # Debugging step
        else:
            print("Product already added to cart:", product_id) #Debugging step

    def __len__(self):
        return len(self.cart)

