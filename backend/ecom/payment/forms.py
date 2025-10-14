from django import forms
from .models import ShippingAddress
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Seller
from .models import NewsletterSubscriber


class NewsletterSubscriberForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email'] # We only require the email address
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email for updates'
            })
        }

class SellerSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    business_name = forms.CharField(max_length=200, required=False)
    business_email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "business_name", "business_email", "phone")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")
        if commit:
            user.is_active = True
            user.save()
            Seller.objects.create(
                user=user,
                business_name=self.cleaned_data.get("business_name"),
                business_email=self.cleaned_data.get("business_email"),
                phone=self.cleaned_data.get("phone")
            )
        return user

class SellerLoginForm(AuthenticationForm):
    pass

class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = [
            'business_name', 'business_description', 'business_email',
            'phone', 'business_address', 'logo', 'bank_account_name',
            'bank_account_number', 'bank_name', 'is_active', 'city', 'country'
        ]


# payment/decorators.py

from django import forms
from .models import ShippingAddress # Assuming ShippingAddress is imported from .models

class ShippingForm(forms.ModelForm):

    # Use consistent styling (label="" and 'class': 'form-control ') for all fields

    # Contact Details
    shipping_full_name = forms.CharField(
        label="", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    shipping_email = forms.CharField(
        label="", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    phone_number = forms.CharField(
        max_length=20, 
        label="", # Consistent with other fields
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (e.g., 0977XXXXXX)'}) # Added form-control class
    )
    
    # Address Details
    shipping_address1 = forms.CharField(
        label="", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address 1'})
    )
    shipping_address2 = forms.CharField(
        label="", 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address 2 (Optional)'})
    )
    shipping_city = forms.CharField(
        label="", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'})
    )
    shipping_province = forms.CharField(
        label="", 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province (Optional)'})
    )
    shipping_postal_code = forms.CharField(
        label="", 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code (Optional)'})
    )
    shipping_country = forms.CharField(
        label="", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'})
    )

    class Meta:
        model = ShippingAddress
        
        # Explicitly defining fields here ensures consistent order, 
        # even though they are all defined above.
        fields = [
            'shipping_full_name', 'shipping_email', 'phone_number', 
            'shipping_address1', 'shipping_address2', 'shipping_city', 
            'shipping_province', 'shipping_postal_code', 'shipping_country'
        ]

        exclude = ['user'] # Keep this for security/logic

        
class PaymentForm(forms.Form):
    card_name = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Name On Card'}), required=True)
    card_number = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Card Number'}), required=True)
    card_exp_date = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Expiration'}), required=True)
    card_cvv_number = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'CVV Code'}), required=True)
    card_address1 = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Billing Address 1'}), required=True)
    card_address2 = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Billing Address 2'}), required=False)
    card_city = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Billing City'}), required=True)
    card_province = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Province'}), required=True)
    card_postal_code = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Billing Postal Code'}), required=True)
    card_country = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Billing Country'}), required=True)




    