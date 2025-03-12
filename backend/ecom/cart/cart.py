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

    def cart_total(self):
        #get the products
        product_ids = self.cart.keys()
        #lookup the keys in the database model
        products = Product.objects.filter(id__in=product_ids)
        quantities = self.cart
        #start counting at 0
        total = 0
        for key, value in quantities.items():
            #convert key string to integer
            key = int(key)
            for product in products:
                if product.id == key:
                    if product.is_sale:
                        total = total + (product.sale_price * value)
                    else:
                        total = total + (product.price * value)
        return total            




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
        # Get the quantities
        quantities = self.cart
        return quantities
    
    def update(self, product, quantity):
        product_id = str(product)
        product_qty = int(quantity)
        # Debugging: Print the product_id and product_qty
        print("Updating product:", product_id, "with quantity:", product_qty)
        # Update the cart
        self.cart[product_id] = product_qty
        # Debugging: Print the updated cart
        print("Updated cart:", self.cart)
        # Update the session
        self.session.modified = True
        return self.cart
    
    def delete(self, product):
        product_id = str(product)
        #delete from dictionary/cart
        if product_id in self.cart:
            del self.cart[product_id]
            self.session.modified = True
    






        #product_id = str(product)
        #product_qty = int(quantity)
        #logic
        #outcart = self.cart
        #update dictionary/cart
        #outcart[product_id] = product_qty
        #update session 
        #self.session.modified = True
        #thing = self.cart
        #return thing
       # self.cart[product_id] = product_qty
        #self.session.modified = True


