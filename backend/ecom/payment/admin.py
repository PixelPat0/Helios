from django.contrib import admin
from .models import ShippingAddress, Order, OrderItem

#register the model on the admin section
admin.site.register(ShippingAddress)
admin.site.register(OrderItem)
admin.site.register(Order)
