# payment/models.py
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from store.models import Customer



class Notification(models.Model):
    """
    Model for internal site notifications (e.g., new orders, system alerts).
    """
    # Links to the User who should receive the notification (Admin or Seller)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    
    # The content of the notification
    message = models.CharField(max_length=255)
    
    # Link to the object that triggered the notification (e.g., the Order)
    # Using GenericForeignKey is often complex for MVPs, so we'll keep it simple for now.
    order_id = models.IntegerField(null=True, blank=True)

    # Status
    is_read = models.BooleanField(default=False)
    
    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Internal Notification"
        verbose_name_plural = "Internal Notifications"

    def __str__(self):
        return f"Notif for {self.user.username}: {self.message[:30]}..."

class NewsletterSubscriber(models.Model):
    """
    Stores email addresses for the project's newsletter subscribers.
    """
    email = models.EmailField(unique=True, max_length=254)
    name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Set to False to unsubscribe")
    date_subscribed = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"
        


class ImpactFundTransaction(models.Model):
    """
    Model to track contributions to the Impact Fund.
    """

# Type pf transaction (SALE_COMMISSION, DONATION, EXPENSE)
    TRANSACTION_CHOICES = [
        ('COMMISSION', 'Sales Commission Allocation'),
        ('DONATION', 'Direct Donation'),
        ('EXPENSE', 'Project Expense/Disbursement'),
    ]
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Link the user/order that triggered the transaction
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, 
        help_text="Transactions for the current active project fund goal.")
    
    def __str__(self):
        return f"{self.transaction_type} of {self.amount}"

    class Meta:
        # We can calculate the running total easily by summing the 'amount' field
        # (Expenses would be recorded as negative amounts)
        pass 

# -----------------------
# ShippingAddress
# -----------------------
class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    shipping_full_name = models.CharField(max_length=255)
    shipping_email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    shipping_address1 = models.CharField("Address Line 1", max_length=255)
    shipping_address2 = models.CharField("Address Line 2", max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=255)
    shipping_province = models.CharField(max_length=255, null=True, blank=True)
    shipping_postal_code = models.CharField(max_length=20, null=True, blank=True)
    shipping_country = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Shipping Address"
        verbose_name_plural = "Shipping Addresses"

    def __str__(self):
        return f'{self.shipping_full_name}, {self.shipping_address1}, {self.shipping_city}, {self.shipping_country}'


# -----------------------
# Seller (new)
# -----------------------
class Seller(models.Model):
    """
    Seller profile linked 1:1 to auth.User.
    Keep fields minimal for now — add more later as needed.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="seller_profile")
    business_name = models.CharField(max_length=200, blank=True, null=True)
    business_description = models.TextField(blank=True, null=True)
    business_email = models.EmailField(max_length=254, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    business_address = models.CharField(max_length=300, blank=True, null=True)
    logo = models.ImageField(upload_to='profile_pics/sellers/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # optional payout info
    bank_account_name = models.CharField(max_length=200, blank=True, null=True)
    bank_account_number = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=150, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Seller Profile"

    @property
    def shop_name(self):
        return self.business_name or (self.user.username if self.user else None)

    def __str__(self):
        return self.shop_name or f"Seller:{self.pk}"


# -----------------------
# Order
# -----------------------
class Order(models.Model):
    ORDER_STATUS = (
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_CHOICES = (
        ('airtel', 'Airtel Money'),
        ('mtn', 'MTN Mobile Money'),
        ('zamtel', 'Zamtel Kwacha'),
        ('card', 'Bank Card'),
        ('cod', 'Cash on Delivery'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    shipping_address = models.TextField(max_length=1000, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    date_ordered = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, null=True, blank=True)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    date_paid = models.DateTimeField(null=True, blank=True)
    date_processed = models.DateTimeField(null=True, blank=True)
    date_shipped = models.DateTimeField(null=True, blank=True)
    date_delivered = models.DateTimeField(null=True, blank=True)
    cancellation_notes = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-date_ordered']),
            models.Index(fields=['-date_shipped']),
        ]

    def __str__(self):
        return f'Order - {self.id}'

    def update_status(self, new_status):
        now = timezone.now()

        if new_status not in dict(self.ORDER_STATUS):
            raise ValueError(f"Invalid status: {new_status}")

        self.status = new_status
        if new_status == 'paid' and not self.date_paid:
            self.date_paid = now
        elif new_status == 'processing' and not self.date_processed:
            self.date_processed = now
        elif new_status == 'shipped' and not self.date_shipped:
            self.date_shipped = now
        elif new_status == 'delivered' and not self.date_delivered:
            self.date_delivered = now

        self.save()


@receiver(pre_save, sender=Order)
def set_shipped_date_on_update(sender, instance, **kwargs):
    """Set date_shipped when status moves to shipped."""
    if not instance.pk:
        return
    try:
        old_order = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return
    if old_order.status != 'shipped' and instance.status == 'shipped' and not instance.date_shipped:
        instance.date_shipped = timezone.now()


# -----------------------
# OrderItem
# -----------------------
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    # Use a string reference to avoid circular imports
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveBigIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Commission config!!
    COMMISSION_RATE = Decimal('0.15')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4, default=COMMISSION_RATE,
                                          help_text="Decimal (0.15 = 15%)")
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Seller now references the new Seller model
    seller = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # If product has a seller (Product.seller -> Seller), set it automatically
        if self.product and getattr(self.product, 'seller', None):
            self.seller = self.product.seller

        # compute commission amount safely
        try:
            item_total = Decimal(self.price) * Decimal(self.quantity)
            self.commission_amount = (item_total * Decimal(self.commission_rate)).quantize(Decimal('0.01'))
        except Exception:
            self.commission_amount = Decimal('0.00')

        super().save(*args, **kwargs)

    def get_seller_earnings(self):
        item_total = Decimal(self.price) * Decimal(self.quantity)
        return item_total - self.commission_amount

    def __str__(self):
        return f'OrderItem - {self.id}'
