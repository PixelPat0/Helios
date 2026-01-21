# Code Comments Reference - Future API Integration Points

This file maps out exactly where to make changes when integrating payment APIs.
Each section shows the current MVP code with comments marking integration points.

---

## 1. payment/utils.py - PaymentProcessor Class

**Current Location:** Lines 55-105

```python
class PaymentProcessor:
    """
    Abstract payment processor - MVP vs Future API.
    """
    
    @staticmethod
    def process_payment(order, payment_method, payment_reference=None):
        """
        # ==================== MVP (CURRENT - TEMPORARY) ====================
        # 
        # This method currently just records the payment attempt and returns 
        # success. Actual verification happens manually in Django admin.
        #
        # ==================== FUTURE (API INTEGRATION) ====================
        #
        # Replace this entire method with real API calls.
        # Pattern: 
        #   if payment_method == 'payfast':
        #       return PayfastProcessor.charge(order, amount)
        #   elif payment_method == 'airtel':
        #       return AirtelProcessor.charge(order, amount)
        #   else:
        #       return CodProcessor.charge(order, amount)
        #
        # The API should return:
        #   {
        #       'success': True/False,
        #       'message': str,
        #       'requires_manual_verification': False,  # Different from MVP!
        #       'transaction_id': str (if successful),
        #       'redirect_url': str (if customer needs to go to payment page)
        #   }
        #
        # See PAYMENT_API_EXAMPLES.md for template code.
        """
        
        # ========== CHANGE THIS SECTION FOR API INTEGRATION ==========
        if not payment_method:
            return {
                'success': False,
                'message': 'Payment method is required',
                'requires_manual_verification': False
            }
        
        # MVP: Just record the attempt
        order.payment_method = payment_method
        order.payment_reference = payment_reference
        order.save()
        
        return {
            'success': True,
            'message': f'Payment submitted for verification ({payment_method})',
            'transaction_id': payment_reference,
            'requires_manual_verification': True,  # ← Key difference
            'instruction': 'Admin will verify payment in Django admin'
        }
        # ================================================================
```

**Integration Checklist:**
- [ ] Create `payment/integrations/payfast.py`
- [ ] Create `payment/integrations/airtel.py` (if needed)
- [ ] Replace MVP section with provider-specific logic
- [ ] Update return value to include redirect_url (if applicable)
- [ ] Set `requires_manual_verification: False`

---

## 2. payment/views.py - process_order Function

**Current Location:** Lines 480-620

```python
def process_order(request):
    """
    Process order and payment.
    """
    
    # Lines 520-540: Order creation
    
    # ==================== PAYMENT PROCESSING SECTION ====================
    # This is where you integrate the API.
    #
    # Current MVP flow:
    #   1. PaymentProcessor.process_payment() returns success
    #   2. Redirect to payment_pending (manual verification)
    #
    # Future API flow:
    #   1. PaymentProcessor.process_payment() calls real API
    #   2. If success, redirect to payment gateway (for card/etc)
    #   3. OR redirect to payment_pending (for mobile money)
    #   4. Payment provider calls webhook when confirmed
    #   5. Webhook handler auto-confirms payment
    #
    # =====================================================================
    
    payment_result = PaymentProcessor.process_payment(
        order, 
        payment_method, 
        payment_reference
    )
    
    # ======== MODIFY THIS SECTION FOR API INTEGRATION ========
    if not payment_result['success']:
        message.error(request, payment_result['message'])
        return redirect('checkout')
    
    # Log the payment attempt for auditing
    log_payment_attempt(order, payment_method, amount_paid)
    # ============================================================
    
    # Create order...
    # Create order items...
    # Send notifications...
    
    # ======== MODIFY REDIRECT FOR API INTEGRATION ========
    # Current: Always show payment instructions
    if payment_result['requires_manual_verification']:
        # MVP: Manual verification needed
        return redirect('payment_pending', order_id=order.id)
    elif 'redirect_url' in payment_result:
        # API: Customer needs to go to payment gateway
        return redirect(payment_result['redirect_url'])
    else:
        # API with auto-confirmation: Show success
        return redirect('payment_success')
    # =======================================================
```

**Integration Checklist:**
- [ ] Update redirect logic to handle API responses
- [ ] Add handling for `redirect_url` from payment gateway
- [ ] Create webhook URL route (see next section)
- [ ] Test with payment provider's sandbox

---

## 3. payment/views.py - Add Webhook Handler

**New Function (Add at end of file, before line 894)**

```python
# ==================== WEBHOOK HANDLER (FOR API INTEGRATION) ====================
#
# This handler receives payment confirmation from the payment provider.
# Currently not used in MVP, but add it now for future API.
#
# When to implement:
#   - After choosing payment provider (Payfast, Airtel, etc.)
#   - Provider will call this URL when payment is confirmed
#   - Webhook must verify signature to prevent fraud
#   - Update PaymentConfirmation.confirm_payment_received() call
#
# Steps:
#   1. Copy webhook code from PAYMENT_API_EXAMPLES.md
#   2. Paste it at end of this file
#   3. Add URL to payment/urls.py (see next section)
#   4. Update webhook URL in payment provider's dashboard
#   5. Test with payment provider's webhook testing tool
#
# ============================================================================

# [WILL ADD WEBHOOK HANDLER HERE WHEN INTEGRATING API]
```

**Integration Checklist:**
- [ ] Copy webhook code from PAYMENT_API_EXAMPLES.md
- [ ] Add webhook function to payment/views.py
- [ ] Add @csrf_exempt decorator
- [ ] Verify webhook signature
- [ ] Call PaymentConfirmation.confirm_payment_received()
- [ ] Log webhook processing
- [ ] Handle errors gracefully

---

## 4. payment/urls.py - Add Webhook URL

**Current File (Lines 1-42)**

```python
# payment/urls.py

urlpatterns = [
    # ... existing URLs ...
    
    path('process_order/', views.process_order, name='process_order'),
    path('payment_pending/<int:order_id>/', views.payment_pending, name='payment_pending'),
    
    # ========== ADD WEBHOOK URL HERE FOR API INTEGRATION ==========
    # When integrating API, add:
    #   path('webhook/payment/', views.payment_webhook, name='payment_webhook'),
    #   path('payment_success/', views.payment_success, name='payment_success'),
    # 
    # The webhook URL must match what you register with payment provider.
    # Example: https://helios.example.com/payment/webhook/payment/
    # ===============================================================
    
    # ... rest of URLs ...
]
```

**Integration Checklist:**
- [ ] Add webhook URL to urlpatterns
- [ ] Make sure webhook URL is public (not login_required)
- [ ] Use @csrf_exempt on webhook view
- [ ] Add payment_success URL

---

## 5. settings.py - Add API Credentials

**Current File (Lines 107-110)**

```python
# Email (env-driven)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@helios.example')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')

# MVP Payment System Settings
BROTHER_PHONE_NUMBER = os.getenv('BROTHER_PHONE_NUMBER', '+260977XXXXXX')
BROTHER_NAME = os.getenv('BROTHER_NAME', 'Helios Zambia (Brother Account)')
BUSINESS_CONTACT_EMAIL = os.getenv('BUSINESS_CONTACT_EMAIL', 'helios.zambia@example.com')

# ========== ADD PAYMENT API SETTINGS HERE ==========
# When integrating API, add:
#
# # Payment Provider Choice
# PAYMENT_PROVIDER = os.getenv('PAYMENT_PROVIDER', 'manual')  # manual, payfast, airtel
#
# # Payfast (if using)
# PAYFAST_MERCHANT_ID = os.getenv('PAYFAST_MERCHANT_ID')
# PAYFAST_MERCHANT_KEY = os.getenv('PAYFAST_MERCHANT_KEY')
# PAYFAST_API_KEY = os.getenv('PAYFAST_API_KEY')
# PAYFAST_SANDBOX = os.getenv('PAYFAST_SANDBOX', 'true') == 'true'
#
# # Airtel (if using)
# AIRTEL_API_KEY = os.getenv('AIRTEL_API_KEY')
# AIRTEL_API_SECRET = os.getenv('AIRTEL_API_SECRET')
#
# # Webhook security
# WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
# ===================================================

CRISPY_TEMPLATE_PACK = 'bootstrap4'
```

**Integration Checklist:**
- [ ] Add PAYMENT_PROVIDER setting
- [ ] Add provider-specific credentials
- [ ] Add WEBHOOK_SECRET setting
- [ ] Update .env with actual credentials
- [ ] Keep .env.example updated

---

## 6. .env File - Add API Credentials

**Current MVP Settings:**

```
BROTHER_PHONE_NUMBER=+260977123456
BROTHER_NAME=Helios Zambia (Brother Account)
BUSINESS_CONTACT_EMAIL=helios.zambia@gmail.com
```

**When Integrating API, Add:**

```
# ========== API INTEGRATION - Add when ready ==========
#
# PAYMENT_PROVIDER=payfast
#
# # Payfast Credentials
# PAYFAST_MERCHANT_ID=10000001
# PAYFAST_MERCHANT_KEY=tk94xu3j4
# PAYFAST_API_KEY=pk_test_abcd1234efgh5678
# PAYFAST_SANDBOX=false
#
# # Webhook security
# WEBHOOK_SECRET=your-secret-webhook-key
# ======================================================
```

**Integration Checklist:**
- [ ] Never commit .env to GitHub (use .env.example)
- [ ] Update settings.py to read these variables
- [ ] Test with sandbox credentials first
- [ ] Switch to production credentials when ready

---

## 7. payment/admin.py - Update Actions

**Current Code (Lines 67-95)**

```python
def confirm_payment_received(self, request, queryset):
    """
    Admin action to manually confirm payment received.
    
    # ========== MVP ONLY: REMOVE THIS WHEN USING API ==========
    # 
    # This action is only for MVP (manual verification).
    # When you integrate real payment API:
    #
    # 1. Payments are confirmed automatically via webhook
    # 2. This admin action is no longer needed
    # 3. Admin can still manually confirm if webhook fails
    # 4. Keep as backup, but mark as "EMERGENCY ONLY"
    #
    # Lines to remove when using API:
    #   - This entire confirm_payment_received() method
    #   - Or comment it out and add note: "[DEPRECATED - API Integration Active]"
    #
    # The webhook will handle confirmation automatically:
    #   payment_webhook() → PaymentConfirmation.confirm_payment_received()
    # 
    # ========================================================
    """
    
    updated_count = 0
    
    for order in queryset:
        result = PaymentConfirmation.confirm_payment_received(order)
        if result['success']:
            updated_count += 1
    
    if updated_count > 0:
        self.message_user(request, f"✓ {updated_count} order(s) marked as PAID.")
```

**Integration Checklist:**
- [ ] Keep this method as backup/emergency only
- [ ] Add comment: "This is backup manual confirmation"
- [ ] Keep webhook-based confirmation as primary
- [ ] Monitor webhook logs for failures

---

## Complete Integration Timeline

```
NOW (MVP):
├─ PaymentProcessor.process_payment() → Returns success
├─ Admin manually confirms in Django admin
└─ Order marked as paid

WEEK 1-2 (Preparation):
├─ Choose payment provider (Payfast recommended)
├─ Get API credentials
├─ Read provider's API documentation
└─ Create test account/sandbox

WEEK 2-3 (Implementation):
├─ Create payment/integrations/payfast.py
├─ Update PaymentProcessor.process_payment()
├─ Add webhook handler to views.py
├─ Add webhook URL to urls.py
├─ Update settings.py with credentials
└─ Test with sandbox

WEEK 3-4 (Testing):
├─ Test full payment flow
├─ Verify webhook receives calls
├─ Check order status updates
├─ Verify emails send correctly
└─ Test error handling

WEEK 4+ (Production):
├─ Deploy to production
├─ Update webhook URL in provider dashboard
├─ Monitor first few payments
├─ Keep manual verification as backup
└─ Migrate remaining manual orders
```

---

## Quick Code Snippets for Integration

### Replace PaymentProcessor.process_payment():

```python
# OLD MVP:
return {
    'success': True,
    'requires_manual_verification': True,
}

# NEW API:
if payment_method == 'payfast':
    from .integrations.payfast import PayfastProcessor
    return PayfastProcessor.charge(order, amount)
elif payment_method == 'airtel':
    from .integrations.airtel import AirtelProcessor
    return AirtelProcessor.charge(order, amount)
else:
    # Cash on Delivery
    return {
        'success': True,
        'requires_manual_verification': False,
        'message': 'COD order created'
    }
```

### Add to process_order() for API response handling:

```python
# Handle API responses
if payment_result.get('redirect_url'):
    # Customer needs to go to payment gateway
    return redirect(payment_result['redirect_url'])
elif not payment_result['requires_manual_verification']:
    # Order is auto-confirmed (webhook will come later)
    return redirect('payment_success', order_id=order.id)
else:
    # Still using manual verification (MVP mode)
    return redirect('payment_pending', order_id=order.id)
```

### Add webhook handler to views.py:

```python
@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    # Get webhook data
    data = json.loads(request.body) if request.content_type == 'application/json' else request.POST.dict()
    
    # Verify signature
    # (Provider-specific)
    
    # Get order
    order = Order.objects.get(id=data['custom_str1'])
    
    # Confirm payment
    result = PaymentConfirmation.confirm_payment_received(order, verified_amount=data['amount'])
    
    if result['success']:
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': result['message']}, status=500)
```

---

## Files to NOT Modify for API

✅ **These don't change:**
- `payment/models.py` - Order model schema is fine
- `payment/forms.py` - Forms remain same
- `payment/templates/payment_pending.html` - Still valid
- Database schema - No new migrations needed

❌ **These change:**
- `payment/utils.py` - PaymentProcessor implementation
- `payment/views.py` - Add webhook handler + redirect logic
- `payment/admin.py` - Optional, can keep manual verification
- `payment/urls.py` - Add webhook URL
- `settings.py` - Add API credentials
- `.env` - Add API credentials

---

## Testing Your Integration

```python
# In Django shell:
python manage.py shell

from payment.integrations.payfast import PayfastProcessor
from payment.models import Order

# Create test order
order = Order.objects.create(
    full_name='Test Customer',
    email='test@example.com',
    amount_paid=Decimal('50.00'),
    status='pending'
)

# Test payment processor
result = PayfastProcessor.charge(order)
print(result)

# Should return:
# {
#     'success': True,
#     'transaction_id': 'txn_123456',
#     'payment_url': 'https://...',
#     'requires_manual_verification': False
# }
```

---

**This file is your integration roadmap.**  
**Refer back to it when you're ready to upgrade from MVP.**

Last Updated: January 21, 2026  
Version: 1.0
