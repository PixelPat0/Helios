# store/models.py
from django.db import models
import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings

def user_directory_path(instance, filename):
    return f'profile_pics/user_{instance.user.id}/{filename}'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_modified = models.DateTimeField(auto_now=True)  # FIXED
    profile_picture = models.ImageField(upload_to=user_directory_path, default='profile_pics/default.jpg', blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    gender = models.CharField(null=True, max_length=10, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    marital_status = models.CharField(max_length=20, choices=[
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    ], blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    province = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    old_cart = models.CharField(max_length=200, blank=True, null=True)
    business_email = models.EmailField(max_length=254, blank=True, null=True)
    TEST_SELLER_EMAIL = 'test.seller@example.com'

    def get_business_email(self):
        if getattr(settings, 'DEBUG', False):
            return self.TEST_SELLER_EMAIL
        return self.business_email or self.user.email

    def __str__(self):
        return self.user.username

def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

post_save.connect(create_profile, sender=User)


class Category(models.Model):
    name = models.CharField(max_length=200)
    class Meta:
        verbose_name_plural = 'categories'
    def __str__(self):
        return self.name


class Customer(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    phone = models.CharField(max_length=100)
    password = models.CharField(max_length=200)
    def __str__(self):
        return self.first_name


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    description = models.CharField(max_length=1000, default='', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    image = models.ImageField(upload_to='uploads/products/', blank=True, null=True)
    is_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    
    # <- IMPORTANT: string ref to payment.Seller to avoid circular import
    seller = models.ForeignKey(
        'payment.Seller',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    def __str__(self):
        return self.name
