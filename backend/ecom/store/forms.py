from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm
from django import forms
from .models import Profile, Product, QuoteRequest
from payment.models import NewsletterSubscriber

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'is_sale', 'sale_price', 'category', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Product Description', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price'}),
            'is_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Sale Price'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }




class UserInfoForm(forms.ModelForm):
    phone = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control ', 'placeholder': 'Phone Number'}), required=False)
    address = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}), required=False)
    city = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}), required=False)
    province = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province'}), required=False)
    country = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}), required=False)

    class Meta:
        model = Profile
        fields = (
            'profile_picture', 'national_id', 'gender', 'date_of_birth', 'occupation',
            'marital_status', 'phone', 'address', 'city', 'province', 'country'
        )
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
        


class ChangePasswordForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']

    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

        self.fields['new_password1'].widget.attrs['class'] = 'form-control'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['new_password1'].label = ''
        self.fields['new_password1'].help_text = (
            '<ul class="form-text text-muted small">'
            '<li>Your password can\'t be too similar to your other personal information.</li>'
            '<li>Your password must contain at least 8 characters.</li>'
            '<li>Your password can\'t be a commonly used password.</li>'
            '<li>Your password can\'t be entirely numeric.</li>'
            '</ul>'
        )

        self.fields['new_password2'].widget.attrs['class'] = 'form-control'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Confirm Password'
        self.fields['new_password2'].label = ''
        self.fields['new_password2'].help_text = (
            '<span class="form-text text-muted">'
            '<small>Enter the same password as before, for verification.</small>'
            '</span>'
        )


class UpdateUserForm(UserChangeForm):
    # Hide the password field
    password = None
    email = forms.EmailField(
        label="",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),required=False
    )
    first_name = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),required=False
    )
    last_name = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),required=False
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'User Name'
        self.fields['username'].label = ''
        self.fields['username'].help_text = (
            '<span class="form-text text-muted">'
            '<small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small>'
            '</span>'
        )


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        label="",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    first_name = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'User Name'
        self.fields['username'].label = ''
        self.fields['username'].help_text = (
            '<span class="form-text text-muted">'
            '<small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small>'
            '</span>'
        )

        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password1'].label = ''
        self.fields['password1'].help_text = (
            '<ul class="form-text text-muted small">'
            '<li>Your password can\'t be too similar to your other personal information.</li>'
            '<li>Your password must contain at least 8 characters.</li>'
            '<li>Your password can\'t be a commonly used password.</li>'
            '<li>Your password can\'t be entirely numeric.</li>'
            '</ul>'
        )

        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
        self.fields['password2'].label = ''
        self.fields['password2'].help_text = (
            '<span class="form-text text-muted">'
            '<small>Enter the same password as before, for verification.</small>'
            '</span>'
        )


# ---------------------------------------------------------
# QUOTE REQUEST FORM
# ---------------------------------------------------------

class QuoteRequestForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = [
            'contact_name', 'contact_email', 'contact_phone',
            'location_city', 'location_province',
            'project_type', 'system_type',
            'daily_energy_usage_kwh', 'current_voltage',
            'appliances_to_run', 'roof_type',
            'budget_range', 'timeline', 'additional_notes'
        ]
        widgets = {
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'location_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Lusaka, Ndola'}),
            'location_province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province'}),
            'project_type': forms.Select(attrs={'class': 'form-select'}),
            'system_type': forms.Select(attrs={'class': 'form-select'}),
            'daily_energy_usage_kwh': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'kWh per day', 'step': '0.01'}),
            'current_voltage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Single Phase (220V) or Three Phase (380V)'}),
            'appliances_to_run': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'List appliances (e.g., 1 Fridge, 5 Lights, 1 TV, Borehole Pump)', 'rows': 4}),
            'roof_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Metal Sheet (ITR), Tile, Concrete Slab'}),
            'budget_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., K20,000 - K50,000'}),
            'timeline': forms.Select(attrs={'class': 'form-select'}),
            'additional_notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Any additional notes...', 'rows': 3}),
        }


class NewsletterForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'style': 'background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: white;'
        })
    )