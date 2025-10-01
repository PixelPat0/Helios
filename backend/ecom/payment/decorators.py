# payment/decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def seller_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'seller_profile'):
            seller_profile = request.user.seller_profile
            # Check if the seller profile is active
            if seller_profile.is_active:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Your seller account is not yet active. Please wait for approval.")
                return redirect('home')
        messages.error(request, "You must be logged in as a seller to view this page.")
        return redirect('seller_login')
    return _wrapped_view