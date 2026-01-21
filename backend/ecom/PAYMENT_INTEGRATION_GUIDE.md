# Payment Integration Guide

## Current Status (MVP)

**Type:** Manual Payment Verification  
**Provider:** Brother's Mobile Money Account  
**Status:** ✅ WORKING - Safe for 10-15 orders  

### How It Works

1. Customer checks out → Order created with `payment_code`
2. Customer shown payment instructions with unique code
3. Customer pays to brother's account with code reference
4. You manually verify payment in Django Admin
5. Click action: "✓ Confirm Payment Received"
6. Order automatically marked as `paid`
7. Email sent to customer

---

## Integration Points (For Future API)

When you're ready to integrate a real payment gateway, here are the **ONLY** files you need to modify:

### 1. **`payment/utils.py`** (PRIMARY)

**Current Method:**
```python
class PaymentProcessor:
    @staticmethod
    def process_payment(order, payment_method, payment_reference=None):
        # MVP: Simply returns success, manual verification in admin
        return {'success': True, 'requires_manual_verification': True}
```

**What to Change (For API):**
```python
# Replace the MVP section with API calls:
if payment_method == 'payfast':
    from .integrations.payfast import PayfastProcessor
    return PayfastProcessor.charge(order, amount)

elif payment_method == 'zamtel':
    from .integrations.zamtel import ZamtelProcessor
    return ZamtelProcessor.charge(order, amount)
```

### 2. **`payment/views.py`** (SECONDARY)

**Current Code in `process_order()`:**
```python
# Line ~540: Payment processing
payment_result = PaymentProcessor.process_payment(order, payment_method, payment_reference)

if payment_result['success']:
    if payment_result['requires_manual_verification']:
        # MVP: Redirect to payment instructions
        return redirect('payment_pending', order_id=order.id)
    else:
        # API: Order already paid (auto-confirmed)
        return redirect('payment_success')
```

**When to Change:** Add webhook handling for async payments

### 3. **`payment/admin.py`** (MINIMAL CHANGE)

**Current Admin Actions:**
```python
def confirm_payment_received(self, request, queryset):
    # Manual confirmation action - only needed for MVP
```

**When to Change:** Remove this action when using API (automatic verification)

### 4. **`.env` File** (FUTURE CREDENTIALS)

Add when integrating API:
```
# Payfast
PAYFAST_MERCHANT_ID=xxxxx
PAYFAST_MERCHANT_KEY=xxxxx
PAYFAST_SANDBOX_MODE=false

# Zamtel API
ZAMTEL_API_KEY=xxxxx
ZAMTEL_API_SECRET=xxxxx

# General
WEBHOOK_SECRET=xxxxx
```

---

## Implementation Checklist for Future API

### Step 1: Create Integration Module

Create folder: `payment/integrations/`

```python
# payment/integrations/payfast.py
from decimal import Decimal
import requests
from django.conf import settings

class PayfastProcessor:
    @staticmethod
    def charge(order, amount):
        """
        Call Payfast API to process payment
        """
        api_key = settings.PAYFAST_API_KEY
        
        payload = {
            'merchant_id': settings.PAYFAST_MERCHANT_ID,
            'merchant_key': settings.PAYFAST_MERCHANT_KEY,
            'amount': float(amount),
            'item_name': f'Helios Order #{order.id}',
            'item_description': f'{len(order.orderitem_set.all())} items',
            'custom_str1': str(order.id),  # Link back to order
            'email_address': order.email,
            'return_url': 'https://helios.com/payment_success/',
            'notify_url': 'https://helios.com/payment_webhook/',
        }
        
        response = requests.post(
            'https://api.payfast.co.zm/v1/charge',
            json=payload,
            headers={'Authorization': f'Bearer {api_key}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'transaction_id': data['transaction_id'],
                'requires_manual_verification': False,
                'redirect_url': data['payment_url']  # Redirect customer
            }
        else:
            return {
                'success': False,
                'message': 'Payment gateway error',
                'requires_manual_verification': False
            }
```

### Step 2: Add Webhook Handler

```python
# payment/views.py - Add new view

@csrf_exempt  # Webhook from payment provider
def payment_webhook(request):
    """
    Webhook callback from payment gateway.
    Provider calls this when payment is confirmed.
    """
    if request.method != 'POST':
        return HttpResponseForbidden()
    
    # Verify webhook signature (provider-specific)
    signature = request.POST.get('signature')
    if not verify_webhook_signature(request.POST, signature):
        logger.warning('Invalid webhook signature')
        return HttpResponse('Invalid signature', status=401)
    
    # Get order
    order_id = int(request.POST.get('custom_str1'))
    order = Order.objects.get(id=order_id)
    
    # Confirm payment
    result = PaymentConfirmation.confirm_payment_received(
        order,
        verified_amount=Decimal(request.POST.get('amount'))
    )
    
    if result['success']:
        logger.info(f'Webhook: Payment confirmed for Order #{order_id}')
        return HttpResponse('OK', status=200)
    else:
        logger.error(f'Webhook: Failed to confirm Order #{order_id}')
        return HttpResponse('Error', status=500)
```

### Step 3: Update Settings

```python
# settings.py

# Payment Gateway Config
PAYMENT_PROVIDER = os.getenv('PAYMENT_PROVIDER', 'manual')  # 'manual', 'payfast', 'zamtel'

# Payfast (if using)
PAYFAST_MERCHANT_ID = os.getenv('PAYFAST_MERCHANT_ID')
PAYFAST_MERCHANT_KEY = os.getenv('PAYFAST_MERCHANT_KEY')
PAYFAST_API_KEY = os.getenv('PAYFAST_API_KEY')
PAYFAST_SANDBOX = os.getenv('PAYFAST_SANDBOX', 'true') == 'true'

# Zamtel (if using)
ZAMTEL_API_KEY = os.getenv('ZAMTEL_API_KEY')
ZAMTEL_API_SECRET = os.getenv('ZAMTEL_API_SECRET')

# Webhook security
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'change-me-in-production')
```

### Step 4: Update process_order() View

```python
# payment/views.py - Modify process_order()

# Around line 540, change this:
payment_result = PaymentProcessor.process_payment(
    order, payment_method, payment_reference
)

# To handle both MVP and API:
if payment_result['requires_manual_verification']:
    # MVP: Show payment instructions
    return redirect('payment_pending', order_id=order.id)

elif 'redirect_url' in payment_result:
    # API: Redirect to payment gateway
    return redirect(payment_result['redirect_url'])

else:
    # API (auto-confirmed): Show success
    return redirect('payment_success')
```

---

## Testing Payment Integration

### Manual Testing (MVP)

1. Create order
2. Go to Django Admin → Orders
3. Verify payment code is generated
4. Click "Confirm Payment Received"
5. Check order status changed to 'paid'
6. Check email was sent

### API Testing (Future)

Use payment provider's sandbox:

```python
# In .env
PAYFAST_SANDBOX=true
PAYFAST_MERCHANT_ID=10000001  # Sandbox ID

# Then run tests
python manage.py test payment.tests.PaymentIntegrationTest
```

---

## Current Payment Fields in Order Model

```python
# These are already set up - no migration needed for API
order.payment_method      # airtel, mtn, zamtel, card, cod
order.payment_reference   # Transaction ID from provider
order.payment_code        # HLS-{ID}-{code} (for manual verification)
order.status              # pending → paid → processing → shipped
order.date_paid           # Auto-set when confirmed
order.amount_paid         # Total amount
```

---

## Common Payment Providers in Zambia

### Payfast
- **API**: ✅ Has REST API
- **Cost**: ~2-3% per transaction
- **Setup**: Merchant account required
- **Integration**: Medium difficulty
- **Status**: ✅ Recommended for MVP upgrade

### Zamtel APIs
- **API**: ⚠️ Limited documentation
- **Cost**: Varies
- **Setup**: Business account + API credentials
- **Integration**: Difficult
- **Status**: ⚠️ Check current status

### Airtel Money
- **API**: ✅ Available
- **Cost**: 1-2% per transaction
- **Setup**: Business account required
- **Integration**: Medium difficulty
- **Status**: ✅ Good option

### Direct Bank Integration
- **API**: ✅ Yes
- **Cost**: Lower (0.5-1%)
- **Setup**: Business account + bank agreement
- **Integration**: Hard
- **Status**: ✅ Best long-term option

---

## Security Checklist for API Integration

- [ ] **HTTPS Only**: Ensure all payment endpoints use HTTPS
- [ ] **API Key Security**: Never commit API keys - use environment variables
- [ ] **Webhook Verification**: Always verify webhook signatures
- [ ] **Rate Limiting**: Add rate limits to prevent abuse
- [ ] **PCI Compliance**: Never store credit card data
- [ ] **Amount Verification**: Always verify amount on server-side
- [ ] **Idempotency**: Handle duplicate webhook calls gracefully
- [ ] **Logging**: Log all payment attempts for audit trail

---

## Files Summary

| File | Purpose | MVP? | Needs API Changes? |
|------|---------|------|-------------------|
| `payment/utils.py` | Payment logic | ✅ Yes | ✅ YES (Primary) |
| `payment/views.py` | Request handling | ✅ Yes | ✅ YES (Secondary) |
| `payment/models.py` | Database schema | ✅ Yes | ❌ No |
| `payment/admin.py` | Manual verification | ✅ Yes | ⚠️ Can remove manual action |
| `payment/urls.py` | URL routing | ✅ Yes | ✅ Add webhook URL |
| `.env` | Configuration | ✅ Yes | ✅ Add API credentials |

---

## Support Resources

- **Payfast Documentation**: https://payfast.co.zm/
- **Django Payments**: https://django-payment.readthedocs.io/
- **Payment Processing**: https://en.wikipedia.org/wiki/Payment_gateway

---

**Next Steps for MVP:**
1. ✅ Manual payment system working
2. ⏳ Get 10-15 orders processed
3. ⏳ Decide on payment provider
4. ⏳ Implement API integration (use checklist above)
5. ⏳ Sunset manual verification

**Timeline Estimate:**
- MVP (current): 0 days (done)
- API integration: 2-3 weeks (depending on provider)
- Full testing: 1-2 weeks
- Production deployment: 1 week
