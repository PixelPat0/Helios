# payment/admin.py
from django.contrib import admin
from .models import Order, OrderItem, ShippingAddress, Seller, NewsletterSubscriber, ImpactFundTransaction


@admin.register(ImpactFundTransaction)
class ImpactFundTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_type', 'amount', 'is_active', 'user', 'date_created')
    list_filter = ('transaction_type', 'is_active', 'date_created')
    search_fields = ('description', 'user__username', 'id')
    
    # 🚨 Action to easily archive multiple transactions
    actions = ['make_inactive']
    
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} transactions successfully marked as inactive/archived.")
    make_inactive.short_description = "Archive selected transactions (Set is_active=False)"


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    # 1. Controls which fields are displayed on the change list page
    list_display = ('email', 'date_subscribed', 'is_active')
    
    # 2. Add search functionality for quick lookups
    search_fields = ('email', 'name')
    
    # 3. Add filters for management (e.g., viewing only active subscribers)
    list_filter = ('is_active', 'date_subscribed')
    
    # 4. Fields displayed when editing a subscriber
    fields = ('email', 'name', 'is_active', 'date_subscribed')
    
    # 5. Make date_subscribed read-only, as it's set automatically
    readonly_fields = ('date_subscribed',)


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
