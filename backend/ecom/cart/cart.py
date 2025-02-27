from store.models import Product

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

    def add(self, product, quantity):
        product_id = str(product.id)
        product_qty = str(quantity)
        #logic
        if product_id not in self.cart:
            #self.cart[product_id] = {'price': str(product.price)}
            self.cart[product_id] = int(product_qty)
            self.session.modified = True
            print("Product added to cart:", product_id) # Debugging step
        else:
            print("Product already added to cart:", product_id) #Debugging step

    def __len__(self):
        return len(self.cart)
    
    def get_prods(self):
        #get ids from cart
        product_ids = self.cart.keys()
        #use ids to lookuo products in the database model
        products = Product.objects.filter(id__in=product_ids)

        #return the looked up products
        return products
    
    def get_quants(self):
        quantities = self.cart #get the quantities
        return quantities


