from django import forms
from .models import ShippingAddress

class ShippingForm(forms.ModelForm):

    shipping_full_name = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Full Name'}), required=True)
    shipping_email = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Email Address'}), required=True)
    shipping_address1 = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Address 1'}), required=True)
    shipping_address2 = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Address 2'}), required=False)
    shipping_city = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'City'}), required=True)
    shipping_province = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Province'}), required=False)
    shipping_postal_code = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Postal Code'}), required=False)
    shipping_country= forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Country'}), required=True)


    class Meta:
        model = ShippingAddress
        fields = [
            'shipping_full_name', 'shipping_email', 'shipping_address1', 
            'shipping_address2', 'shipping_city', 'shipping_province', 
            'shipping_postal_code', 'shipping_country'
        ]

        exclude = ['user',]

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




    