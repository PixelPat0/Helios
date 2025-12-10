# store/admin.py
from django.contrib import admin
from .models import Category, Customer, Product, Profile, QuoteRequest, SellerQuote
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

# ---------------------------
# Register store models safely
# ---------------------------
# Register only store-owned models here. Order is registered in payment.admin.
for model in (Category, Customer, Product, Profile, QuoteRequest, SellerQuote):
    if model not in admin.site._registry:
        admin.site.register(model)

# ---------------------------
# Embed Profile inline into User admin
# ---------------------------
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "profile"

class CustomUserAdmin(DefaultUserAdmin):
    inlines = (ProfileInline,)
    # You can customize list_display, search_fields, etc. here if you want:
    # list_display = DefaultUserAdmin.list_display + ('email',)

# Unregister default User admin and register our extended version safely
if User in admin.site._registry:
    admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
