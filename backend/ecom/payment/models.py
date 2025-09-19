from django.db import models
from django.contrib.auth.models import User
from store.models import Product
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import datetime
from decimal import Decimal

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    shipping_full_name = models.CharField(max_length=255)
    shipping_email = models.EmailField(max_length=255)  # Use EmailField for validation
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

#create a user Shipping Address by default
#create a profile when a user is created
def create_shipping(sender, instance, created, **kwargs):
    if created:
        user_shipping = ShippingAddress(user=instance)
        user_shipping.save()
#automate profile creation
post_save.connect(create_shipping, sender=User)


#create Order model
class Order(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-date_ordered']),
            models.Index(fields=['-date_shipped']),
        ]

    # Define status choices for better tracking
    ORDER_STATUS = (
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    # Define payment method choices
    PAYMENT_CHOICES = (
        ('airtel', 'Airtel Money'),
        ('mtn', 'MTN Mobile Money'),
        ('zamtel', 'Zamtel Kwacha'),
        ('card', 'Bank Card'),
        ('cod', 'Cash on Delivery'),
    )

    # Existing fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    shipping_address = models.TextField(max_length=1000, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    date_ordered = models.DateTimeField(auto_now_add=True)
    
    # New fields for enhanced tracking
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, null=True, blank=True)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)  # For mobile money/card reference
    date_paid = models.DateTimeField(null=True, blank=True)
    date_processed = models.DateTimeField(null=True, blank=True)
    date_shipped = models.DateTimeField(null=True, blank=True)
    date_delivered = models.DateTimeField(null=True, blank=True)
    cancellation_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Order - {str(self.id)}'

    def update_status(self, new_status):
        """Updates order status and corresponding timestamp"""
        from django.utils import timezone
        now = timezone.now()  # Use timezone-aware datetime
        
        # Validate status
        if new_status not in dict(self.ORDER_STATUS):
            raise ValueError(f"Invalid status: {new_status}")
            
        self.status = new_status
        
        # Update corresponding timestamp
        if new_status == 'paid':
            self.date_paid = now
        elif new_status == 'processing':
            self.date_processed = now
        elif new_status == 'shipped':
            self.date_shipped = now
        elif new_status == 'delivered':
            self.date_delivered = now
        
        self.save()

# Remove or update the old signal if it exists
@receiver(pre_save, sender=Order)
def set_shipped_date_on_update(sender, instance, **kwargs):
    """Updates date_shipped when status changes to shipped"""
    try:
        old_order = Order.objects.get(pk=instance.pk)
        if old_order.status != 'shipped' and instance.status == 'shipped':
            instance.date_shipped = datetime.datetime.now()
    except Order.DoesNotExist:
        pass


#create order items model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveBigIntegerField(default=1)
    price = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    COMMISSION_RATE = Decimal('0.15')  # Convert to Decimal
    
    commission_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=COMMISSION_RATE,
        help_text="Commission rate as decimal (e.g., 0.15 for 15%)"
    )
    commission_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    seller = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='sold_items'
    )
    seller_logo = models.ImageField(
        upload_to='seller_logos/', 
        null=True, 
        blank=True
    )

    def save(self, *args, **kwargs):
        # Set seller from product if available
        if self.product and self.product.seller:
            self.seller = self.product.seller
        
        # Calculate commission amount
        self.commission_amount = self.price * self.quantity * self.commission_rate
        
        super().save(*args, **kwargs)

    def __str__(self): 
        return f'Order Item - {str(self.id)}'