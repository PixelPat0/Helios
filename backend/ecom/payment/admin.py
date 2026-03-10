# payment/admin.py
from django.contrib import admin
from .models import Order, OrderItem, ShippingAddress, Seller, NewsletterSubscriber, ImpactFundTransaction
from .utils import PaymentConfirmation


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
    list_display = ('id', 'payment_code', 'full_name', 'email', 'amount_paid', 'status', 'date_ordered')
    list_filter = ('status', 'date_ordered')
    search_fields = ('full_name', 'email', 'id', 'payment_code')
    readonly_fields = ('id', 'date_ordered', 'payment_code')
    inlines = [OrderItemInline]
    actions = ['confirm_payment_received', 'mark_processing', 'mark_shipped']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'user', 'full_name', 'email', 'shipping_address', 'amount_paid', 'date_ordered')
        }),
        ('MVP Payment Tracking', {
            'fields': ('payment_code', 'payment_method', 'payment_reference'),
            'description': 'Payment Code: Customer includes this code when paying to brother\'s account'
        }),
        ('Status and Dates', {
            'fields': ('status', 'date_paid', 'date_processed', 'date_shipped', 'date_delivered')
        }),
    )

    def confirm_payment_received(self, request, queryset):
        """
        Admin action to manually confirm payment received.
        
        MVP: Admin manually verifies payment came in and clicks this action
        Future: This action can be removed when using API integration
                (payment confirmation happens automatically via webhook)
        
        See PAYMENT_INTEGRATION_GUIDE.md for details
        """
        updated_count = 0
        
        for order in queryset:
            result = PaymentConfirmation.confirm_payment_received(order)
            
            if result['success']:
                updated_count += 1
        
        if updated_count > 0:
            self.message_user(request, f"✓ {updated_count} order(s) marked as PAID. Ready for processing.")
        else:
            self.message_user(request, "No pending orders to confirm, or errors occurred.")
    
    confirm_payment_received.short_description = "✓ Confirm Payment Received (Pending → Paid) [MVP ONLY]"

    def mark_processing(self, request, queryset):
        """Admin action to mark orders as processing."""
        updated = queryset.filter(status__in=['paid', 'pending']).update(status='processing')
        if updated > 0:
            self.message_user(request, f"✓ {updated} order(s) moved to PROCESSING.")
    
    mark_processing.short_description = "→ Mark as Processing"

    def mark_shipped(self, request, queryset):
        """Admin action to mark orders as shipped."""
        updated = queryset.filter(status='processing').update(status='shipped')
        if updated > 0:
            self.message_user(request, f"✓ {updated} order(s) marked as SHIPPED.")
    
    mark_shipped.short_description = "📦 Mark as Shipped"


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
