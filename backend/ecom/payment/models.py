from django.db import models
from django.contrib.auth.models import User
from store.models import Product
from django.db.models.signals import post_save

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
    #foreign key to user
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)  # Use EmailField for validation
    shipping_address = models.TextField(max_length=1000, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    date_ordered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order - {str(self.id)}'


#create order items model
class OrderItem(models.Model):
    user = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveBigIntegerField(default=1)
    price = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)


    def __str__(self):
        return f'Order Item - {str(self.id)}'