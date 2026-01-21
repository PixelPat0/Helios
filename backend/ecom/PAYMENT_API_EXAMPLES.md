# Example Payment API Integrations (Templates)

This file contains template code for integrating payment gateways in the future.
Use these as starting points when you're ready to switch from manual verification.

---

## 1. Payfast Integration (Recommended for Zambia)

Create file: `payment/integrations/payfast.py`

```python
"""
Payfast payment processor for Helios.
Payfast: https://payfast.co.zm/
"""

import requests
import logging
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class PayfastProcessor:
    """
    Processes payments through Payfast API.
    
    Payfast is a Zambian payment gateway that supports:
    - Mobile money (Airtel, MTN, Zamtel)
    - Bank cards
    - Bank transfers
    """
    
    BASE_URL = "https://api.payfast.co.zm/v1"
    SANDBOX_URL = "https://sandbox.payfast.co.zm/v1"
    
    @classmethod
    def get_base_url(cls):
        """Get API URL based on environment."""
        if getattr(settings, 'PAYFAST_SANDBOX', True):
            return cls.SANDBOX_URL
        return cls.BASE_URL
    
    @staticmethod
    def charge(order, payment_method='card'):
        """
        Create a payment charge with Payfast.
        
        Args:
            order: Order instance
            payment_method: str (card, mobile_money, etc.)
        
        Returns:
            dict: {
                'success': bool,
                'transaction_id': str,
                'payment_url': str (URL to redirect customer),
                'error': str (if failed)
            }
        """
        
        try:
            # Prepare payment payload
            payload = {
                'amount': float(order.amount_paid),
                'currency': 'ZMW',
                'description': f'Helios Order #{order.id}',
                'reference': order.payment_code,  # Use our payment code
                'email': order.email,
                'phone': order.phone_number,
                'customer_name': order.full_name,
                'metadata': {
                    'order_id': order.id,
                    'customer_email': order.email,
                },
                'redirect_url': _get_redirect_url(order),
                'webhook_url': _get_webhook_url(),
            }
            
            # Make API request
            headers = {
                'Authorization': f'Bearer {settings.PAYFAST_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{PayfastProcessor.get_base_url()}/payments',
                json=payload,
                headers=headers,
                timeout=10
            )
            
            # Handle response
            if response.status_code == 201:
                data = response.json()
                logger.info(f'Payfast charge created for Order #{order.id}')
                
                return {
                    'success': True,
                    'transaction_id': data['transaction_id'],
                    'payment_url': data['payment_url'],
                    'requires_manual_verification': False  # API confirms automatically
                }
            else:
                error_msg = response.json().get('message', 'Payment gateway error')
                logger.error(f'Payfast error for Order #{order.id}: {error_msg}')
                
                return {
                    'success': False,
                    'error': error_msg,
                    'requires_manual_verification': False
                }
        
        except Exception as e:
            logger.exception(f'Payfast exception for Order #{order.id}: {str(e)}')
            return {
                'success': False,
                'error': 'Payment processing error',
                'requires_manual_verification': False
            }
    
    @staticmethod
    def verify_webhook(data, signature):
        """
        Verify that webhook is from Payfast (security check).
        
        Args:
            data: dict - webhook payload
            signature: str - signature from header
        
        Returns:
            bool - True if signature is valid
        """
        import hashlib
        import hmac
        
        # Create signature from data
        message = '&'.join([f'{k}={v}' for k, v in sorted(data.items())])
        expected_signature = hmac.new(
            settings.WEBHOOK_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)


def _get_redirect_url(order):
    """Generate redirect URL after payment."""
    from django.urls import reverse
    from django.conf import settings
    return f"{settings.BASE_URL}/payment_success/?order_id={order.id}"


def _get_webhook_url():
    """Generate webhook URL for payment confirmation."""
    from django.urls import reverse
    from django.conf import settings
    return f"{settings.BASE_URL}/payment_webhook/"
```

### Usage in views.py:

```python
from payment.integrations.payfast import PayfastProcessor

# In process_order():
if settings.PAYMENT_PROVIDER == 'payfast':
    payment_result = PayfastProcessor.charge(order, payment_method)
    
    if payment_result['success']:
        # Redirect customer to Payfast
        return redirect(payment_result['payment_url'])
    else:
        messages.error(request, payment_result['error'])
        return redirect('checkout')
```

---

## 2. Webhook Handler (For Any API)

Add to `payment/views.py`:

```python
"""
Webhook handler for payment confirmations.
Called by payment provider when payment is confirmed.
"""

import json
import logging
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from decimal import Decimal

from .models import Order
from .utils import PaymentConfirmation
from .integrations.payfast import PayfastProcessor

logger = logging.getLogger(__name__)


@csrf_exempt  # Payment provider's servers need to POST without CSRF token
@require_http_methods(["POST"])
def payment_webhook(request):
    """
    Webhook endpoint for payment confirmations.
    
    Called by payment gateway when payment is processed.
    
    IMPORTANT: Always verify webhook signature to prevent fraud
    """
    
    try:
        # Parse webhook data
        if request.content_type == 'application/json':
            webhook_data = json.loads(request.body)
        else:
            webhook_data = request.POST.dict()
        
        # Get signature from header
        signature = request.headers.get('X-Webhook-Signature')
        
        # Verify signature (CRITICAL for security)
        if settings.PAYMENT_PROVIDER == 'payfast':
            if not PayfastProcessor.verify_webhook(webhook_data, signature):
                logger.warning('Invalid Payfast webhook signature')
                return JsonResponse({'error': 'Invalid signature'}, status=401)
        
        # Extract order ID
        # This depends on payment provider - adjust accordingly
        order_id = webhook_data.get('custom_str1') or webhook_data.get('metadata', {}).get('order_id')
        
        if not order_id:
            logger.error('Webhook: No order ID in payload')
            return JsonResponse({'error': 'No order ID'}, status=400)
        
        # Get order
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            logger.error(f'Webhook: Order #{order_id} not found')
            return JsonResponse({'error': 'Order not found'}, status=404)
        
        # Verify payment status
        payment_status = webhook_data.get('status', '').lower()
        if payment_status not in ['completed', 'approved', 'paid']:
            logger.info(f'Webhook: Order #{order_id} payment not completed (status: {payment_status})')
            return JsonResponse({'success': False, 'message': 'Payment not completed'})
        
        # Verify amount
        webhook_amount = Decimal(str(webhook_data.get('amount', 0)))
        if webhook_amount != order.amount_paid:
            logger.error(
                f'Webhook: Amount mismatch for Order #{order_id}. '
                f'Expected K{order.amount_paid}, got K{webhook_amount}'
            )
            return JsonResponse({'error': 'Amount mismatch'}, status=400)
        
        # Confirm payment
        result = PaymentConfirmation.confirm_payment_received(
            order,
            verified_amount=webhook_amount,
            payment_notes=f'Webhook from {settings.PAYMENT_PROVIDER}'
        )
        
        if result['success']:
            logger.info(f'Webhook: Payment confirmed for Order #{order_id}')
            return JsonResponse({'success': True, 'message': 'Payment confirmed'})
        else:
            logger.error(f'Webhook: Failed to confirm Order #{order_id}')
            return JsonResponse({'error': result['message']}, status=500)
    
    except json.JSONDecodeError:
        logger.error('Webhook: Invalid JSON')
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    except Exception as e:
        logger.exception(f'Webhook error: {str(e)}')
        return JsonResponse({'error': 'Internal error'}, status=500)


@csrf_exempt
def payment_success(request):
    """
    Redirect page after successful payment (for non-webhook providers).
    Some payment providers redirect customer back to this page.
    """
    order_id = request.GET.get('order_id')
    
    if not order_id:
        return redirect('home')
    
    try:
        order = Order.objects.get(id=order_id)
        context = {'order': order, 'payment_success': True}
        return render(request, 'payment/payment_success.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('home')
```

### URL for webhook:

Add to `payment/urls.py`:

```python
urlpatterns = [
    # ... existing URLs ...
    
    # Webhook for payment provider confirmation
    path('webhook/payment/', views.payment_webhook, name='payment_webhook'),
    path('payment_success/', views.payment_success, name='payment_success'),
]
```

---

## 3. Airtel Money Integration

Create file: `payment/integrations/airtel.py`

```python
"""
Airtel Money integration for Helios.
Airtel: https://www.airtel.zm/
"""

import requests
import logging
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)


class AirtelProcessor:
    """
    Processes payments through Airtel Money API.
    
    Note: Airtel documentation is limited. Verify with Airtel support.
    """
    
    @staticmethod
    def charge(order, payment_method='airtel'):
        """
        Create an Airtel payment.
        
        NOTE: Implementation depends on Airtel's specific API.
        Contact Airtel for current API details.
        """
        
        try:
            # Placeholder - adjust based on Airtel's actual API
            payload = {
                'msisdn': order.phone_number,  # Customer's phone
                'amount': float(order.amount_paid),
                'reference': order.payment_code,
                'narrative': f'Helios Order #{order.id}',
            }
            
            headers = {
                'Authorization': f'Bearer {settings.AIRTEL_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://api.airtel.com/v1/payments/initiate',  # Check actual endpoint
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'transaction_id': data.get('transaction_id'),
                    'requires_manual_verification': False
                }
            else:
                return {
                    'success': False,
                    'error': 'Airtel payment failed',
                    'requires_manual_verification': False
                }
        
        except Exception as e:
            logger.exception(f'Airtel error: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'requires_manual_verification': False
            }
```

---

## 4. Settings Configuration for API

Add to `settings.py`:

```python
# Payment Provider
PAYMENT_PROVIDER = os.getenv('PAYMENT_PROVIDER', 'manual')

# Payfast
PAYFAST_MERCHANT_ID = os.getenv('PAYFAST_MERCHANT_ID')
PAYFAST_MERCHANT_KEY = os.getenv('PAYFAST_MERCHANT_KEY')
PAYFAST_API_KEY = os.getenv('PAYFAST_API_KEY')
PAYFAST_SANDBOX = os.getenv('PAYFAST_SANDBOX', 'true').lower() == 'true'

# Airtel
AIRTEL_CLIENT_ID = os.getenv('AIRTEL_CLIENT_ID')
AIRTEL_CLIENT_SECRET = os.getenv('AIRTEL_CLIENT_SECRET')
AIRTEL_API_KEY = os.getenv('AIRTEL_API_KEY')

# Webhook security
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'change-me-in-production')
```

---

## How to Implement

1. **Choose provider:** Payfast recommended for Zambia
2. **Copy relevant code** from above
3. **Update `payment/utils.py`:** Replace MVP section with API calls
4. **Add webhook handler** to views.py
5. **Update settings.py** with API credentials
6. **Test with sandbox** first
7. **Deploy to production**
8. **Monitor webhooks** for failures

See `PAYMENT_INTEGRATION_GUIDE.md` for detailed steps.

---

## Testing Webhook Locally

Use ngrok to expose localhost:

```bash
# Install ngrok: https://ngrok.com/
ngrok http 8000

# Copy the URL: https://xxxxx.ngrok.io
# Update your payment provider webhook URL to point to: https://xxxxx.ngrok.io/payment_webhook/

# Now payment provider can reach your local Django server
```

---

## Support

- **Payfast Docs**: https://payfast.co.zm/api
- **Airtel Docs**: Contact Airtel directly
- **Django Docs**: https://docs.djangoproject.com/
- **Webhook Testing**: https://webhook.site/

---

**Last Updated:** January 21, 2026  
**Status:** Template code (not production ready - for reference only)
