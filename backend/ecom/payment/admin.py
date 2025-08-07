from django.contrib import admin
from .models import ShippingAddress, Order, OrderItem
from django.contrib.auth.models import User

#register the model on the admin section
admin.site.register(ShippingAddress)
admin.site.register(OrderItem)
admin.site.register(Order)


#Create and OrderItem Inline
class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0

# Extend our Order Model

class OrderAdmin(admin.ModelAdmin):
    model = Order
    readonly_fields = ["id","date_ordered"]
    fields = ["id", "user", "full_name", "email", "shipping_address", "amount_paid", "date_ordered", "shipped", "date_shipped"]
    inlines = [OrderItemInline]
    
# Unregister the default User model
admin.site.unregister(Order)

#re-register our order AND  OrderItem models
admin.site.register(Order, OrderAdmin)