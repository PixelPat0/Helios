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


# ---------------------------------------------------------
# QUOTE REQUEST SYSTEM
# ---------------------------------------------------------

class QuoteRequest(models.Model):
    """
    Stores detailed requirements for a Solar/Power project.
    """
    PROJECT_TYPE_CHOICES = [
        ('residential', 'Residential (Home)'),
        ('commercial', 'Commercial (Office/Shop)'),
        ('agricultural', 'Agricultural (Farm/Irrigation)'),
        ('industrial', 'Industrial'),
    ]

    SYSTEM_TYPE_CHOICES = [
        ('backup', 'Backup System (Load Shedding only)'),
        ('off_grid', 'Off-Grid (No ZESCO connection)'),
        ('hybrid', 'Hybrid (Solar + Grid + Battery)'),
        ('grid_tie', 'Grid-Tie (Save Bill, No Battery)'),
        ('unsure', 'I am not sure'),
    ]

    TIMELINE_CHOICES = [
        ('immediate', 'Immediately'),
        ('1_month', 'Within 1 month'),
        ('3_months', '1-3 Months'),
        ('planning', 'Just Planning/Budgeting'),
    ]

    # --- 1. Customer Info ---
    # Nullable so we can save the request BEFORE creating the user account if needed
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='quote_requests')
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    location_city = models.CharField(max_length=100, help_text="e.g. Lusaka, Ndola")
    location_province = models.CharField(max_length=100, default='Lusaka')

    # --- 2. Technical Requirements ---
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default='residential')
    system_type = models.CharField(max_length=20, choices=SYSTEM_TYPE_CHOICES, default='hybrid')
    
    # Energy Needs
    daily_energy_usage_kwh = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, 
        help_text="Average daily usage in kWh (check your ZESCO bill)"
    )
    current_voltage = models.CharField(
        max_length=50, blank=True, null=True, 
        help_text="e.g., Single Phase (220V) or Three Phase (380V)"
    )
    
    # Specifics
    appliances_to_run = models.TextField(
        help_text="List key appliances (e.g., 1 Fridge, 5 Lights, 1 TV, Borehole Pump)"
    )
    roof_type = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="e.g., Metal Sheet (ITR), Tile, Concrete Slab"
    )

    # --- 3. Budget & Metadata ---
    budget_range = models.CharField(max_length=100, blank=True, help_text="e.g., K20,000 - K50,000")
    timeline = models.CharField(max_length=20, choices=TIMELINE_CHOICES, default='1_month')
    additional_notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20, 
        choices=[('open', 'Open'), ('processing', 'Processing'), ('closed', 'Closed')], 
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_project_type_display()} Quote - {self.contact_name}"


class SellerQuote(models.Model):
    """
    A specific offer/bid from a Seller in response to a QuoteRequest.
    """
    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name='seller_quotes')
    seller = models.ForeignKey('payment.Seller', on_delete=models.CASCADE, related_name='quotes_submitted')
    
    price = models.DecimalField(max_digits=12, decimal_places=2)
    valid_until = models.DateField(null=True, blank=True)
    
    components_summary = models.TextField(help_text="Summary of panels, inverter, battery brands/sizes")
    installation_included = models.BooleanField(default=True)
    warranty_terms = models.TextField(blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending Review'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote {self.id} by {self.seller}"
