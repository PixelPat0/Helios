from django.contrib import admin
from .models import Order, OrderItem, ShippingAddress

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'amount_paid', 'status', 'date_ordered')
    list_filter = ('status', 'date_ordered')
    search_fields = ('full_name', 'email', 'id')
    readonly_fields = ('date_ordered',)
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'full_name', 'email', 'shipping_address', 'amount_paid', 'date_ordered')
        }),
        ('Status and Payment', {
            'fields': ('status', 'payment_method', 'payment_reference')
        }),
        ('Timestamps', {
            'fields': ('date_paid', 'date_processed', 'date_shipped', 'date_delivered')
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__id', 'product__name')

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'shipping_full_name', 'shipping_email')
    search_fields = ('shipping_full_name', 'shipping_email')