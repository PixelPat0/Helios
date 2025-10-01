# payment/admin.py
from django.contrib import admin
from .models import Order, OrderItem, ShippingAddress, Seller


# Register Seller (safe guard)
if Seller not in admin.site._registry:
    admin.site.register(Seller)


# Inline for OrderItem inside Order admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('commission_amount',)
    extra = 0


# Register Order (single registration)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'amount_paid', 'status', 'date_ordered')
    list_filter = ('status', 'date_ordered')
    search_fields = ('full_name', 'email', 'id')
    readonly_fields = ('date_ordered',)
    inlines = [OrderItemInline]
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


# Register OrderItem (single registration)
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__id', 'product__name')


# Register ShippingAddress (single registration)
@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'shipping_full_name', 'shipping_email')
    search_fields = ('shipping_full_name', 'shipping_email')
