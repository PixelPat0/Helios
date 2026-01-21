"""
Payment utilities and helpers for Helios e-commerce platform.

PAYMENT FLOW ARCHITECTURE:
========================
This module handles payment processing with an abstraction layer that supports
both manual verification (MVP) and future API integration (production).

MVP FLOW (Current - Temporary):
    1. Order created with status='pending'
    2. Customer receives payment instructions with payment code
    3. Customer sends payment to brother's account with payment code reference
    4. Admin manually verifies in Django admin
    5. Admin clicks action: "Confirm Payment Received"
    6. Order status changes to 'paid' automatically

PRODUCTION FLOW (Future - After API Integration):
    1. Order created with status='pending'
    2. Customer sent to payment gateway (Payfast/Zamtel API)
    3. Payment gateway processes payment
    4. Webhook callback confirms payment
    5. Order status changes to 'paid' automatically (no manual step)

INTEGRATION POINTS FOR FUTURE API:
==================================
When you're ready to integrate with Payfast/Zamtel/etc:
    - Replace PaymentProcessor.process_payment() method
    - Add webhook handler in views.py
    - Update settings.py with API credentials
    - No changes needed to Order model or database schema
"""

from decimal import Decimal
from django.utils import timezone
from django.conf import settings
import logging

from .models import Notification, Order

logger = logging.getLogger(__name__)


# =====================================================================
# PAYMENT PROCESSOR - Abstract layer for payment processing
# =====================================================================
class PaymentProcessor:
    """
    Abstract payment processor that can be swapped for different providers.
    
    MVP Implementation: Manual verification
    Future Implementation: Real API (Payfast, Zamtel, etc.)
    """
    
    @staticmethod
    def process_payment(order, payment_method, payment_reference=None):
        """
        Process a payment for an order.
        
        CURRENT (MVP):
            - Returns success (manual verification in admin)
            - Admin confirms in Django admin
        
        FUTURE (API Integration):
            - Call actual payment gateway API
            - Handle async payment processing
            - Return payment gateway response
        
        Args:
            order: Order instance
            payment_method: str (airtel, mtn, zamtel, card, cod)
            payment_reference: str (transaction ID from payment)
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'transaction_id': str (if applicable),
                'requires_manual_verification': bool  # True for MVP, False for API
            }
        """
        
        # =========== MVP IMPLEMENTATION (TEMPORARY) ===========
        # This simply returns success - actual verification happens in admin
        
        if not payment_method:
            return {
                'success': False,
                'message': 'Payment method is required',
                'requires_manual_verification': False
            }
        
        # Store the payment reference and payment method
        order.payment_method = payment_method
        order.payment_reference = payment_reference
        order.save()
        
        return {
            'success': True,
            'message': f'Payment submitted for verification ({payment_method})',
            'transaction_id': payment_reference,
            'requires_manual_verification': True,  # MVP: Manual verification needed
            'instruction': 'Admin will verify payment in Django admin'
        }
        
        # =========== FUTURE API IMPLEMENTATION ===========
        # Replace the above with actual API calls:
        #
        # if payment_method == 'payfast':
        #     from .integrations.payfast import PayfastProcessor
        #     return PayfastProcessor.charge(order, amount)
        # 
        # elif payment_method == 'zamtel':
        #     from .integrations.zamtel import ZamtelProcessor
        #     return ZamtelProcessor.charge(order, amount)
        # 
        # elif payment_method == 'airtel':
        #     from .integrations.airtel import AirtelProcessor
        #     return AirtelProcessor.charge(order, amount)
        # 
        # etc...


# =====================================================================
# PAYMENT CONFIRMATION - Marks order as paid (admin action wrapper)
# =====================================================================
class PaymentConfirmation:
    """
    Handles confirming that a payment has been received.
    
    CURRENT USE: Admin confirms manually after receiving payment
    FUTURE USE: Automatic via webhook callback from payment gateway
    """
    
    @staticmethod
    def confirm_payment_received(order, verified_amount=None, payment_notes=None):
        """
        Confirm that payment has been received for an order.
        
        Call this when:
        - MVP: Admin manually verifies payment in Django admin
        - Future: Webhook callback confirms payment from API
        
        Args:
            order: Order instance
            verified_amount: Decimal (optional - amount that was verified)
            payment_notes: str (optional - notes about the payment)
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'order_status': str
            }
        """
        
        try:
            # Safety check: don't double-confirm
            if order.status == 'paid':
                return {
                    'success': False,
                    'message': f'Order #{order.id} is already marked as paid',
                    'order_status': order.status
                }
            
            # Verify amount matches (if provided)
            if verified_amount:
                if Decimal(str(verified_amount)) != order.amount_paid:
                    logger.warning(
                        f'Payment amount mismatch for Order #{order.id}: '
                        f'Expected K{order.amount_paid}, got K{verified_amount}'
                    )
                    return {
                        'success': False,
                        'message': f'Amount mismatch: Expected K{order.amount_paid}, got K{verified_amount}',
                        'order_status': order.status
                    }
            
            # Update order status
            order.update_status('paid')
            
            # Log the confirmation
            logger.info(
                f'Payment confirmed for Order #{order.id} | '
                f'Amount: K{order.amount_paid} | '
                f'Method: {order.payment_method}'
            )
            
            return {
                'success': True,
                'message': f'Payment confirmed for Order #{order.id}',
                'order_status': order.status,
                'date_paid': order.date_paid
            }
        
        except Exception as e:
            logger.error(f'Error confirming payment for Order #{order.id}: {str(e)}')
            return {
                'success': False,
                'message': f'Error confirming payment: {str(e)}',
                'order_status': order.status
            }


# =====================================================================
# PAYMENT VALIDATION - Validates payment details
# =====================================================================
class PaymentValidator:
    """
    Validates payment details and references.
    """
    
    @staticmethod
    def validate_payment_code(payment_code, order_id=None):
        """
        Validate that a payment code matches the expected format and exists.
        
        Format: HLS-{OrderID}-{3-char-random}
        Example: HLS-1001-A7K2
        """
        
        if not payment_code:
            return {'valid': False, 'error': 'Payment code is required'}
        
        # Parse the payment code
        parts = payment_code.split('-')
        if len(parts) != 3:
            return {'valid': False, 'error': 'Invalid payment code format'}
        
        if parts[0] != 'HLS':
            return {'valid': False, 'error': 'Payment code must start with HLS'}
        
        try:
            code_order_id = int(parts[1])
        except ValueError:
            return {'valid': False, 'error': 'Invalid order ID in payment code'}
        
        # Check if order exists
        try:
            order = Order.objects.get(id=code_order_id)
        except Order.DoesNotExist:
            return {'valid': False, 'error': f'Order #{code_order_id} not found'}
        
        # If order_id was provided, verify it matches
        if order_id and code_order_id != order_id:
            return {'valid': False, 'error': 'Payment code does not match order'}
        
        return {
            'valid': True,
            'order_id': code_order_id,
            'order': order,
            'payment_code': payment_code
        }
    
    @staticmethod
    def validate_payment_amount(amount, order):
        """
        Validate that the payment amount matches the order total.
        """
        
        try:
            amount_decimal = Decimal(str(amount))
        except:
            return {'valid': False, 'error': 'Invalid amount format'}
        
        if amount_decimal != order.amount_paid:
            return {
                'valid': False,
                'error': f'Amount mismatch: expected K{order.amount_paid}, got K{amount_decimal}'
            }
        
        return {'valid': True, 'amount': amount_decimal}


# =====================================================================
# NOTIFICATIONS - Helper for payment-related notifications
# =====================================================================
def create_notification(user, message, order_id=None, quote_request=None):
    """
    Simple helper to create a Notification. Keeps code DRY.
    
    Args:
        user: User object
        message: str - notification message
        order_id: int (optional)
        quote_request: QuoteRequest object (optional)
    
    Returns:
        Notification instance
    """
    return Notification.objects.create(
        user=user,
        message=message,
        order_id=order_id,
        quote_request=quote_request,
        is_read=False,
        created_at=timezone.now()
    )


# =====================================================================
# LOGGING HELPERS - For debugging and auditing
# =====================================================================
def log_payment_attempt(order, payment_method, amount):
    """Log a payment attempt for auditing."""
    logger.info(
        f'Payment attempt - Order #{order.id} | '
        f'Amount: K{amount} | '
        f'Method: {payment_method} | '
        f'Customer: {order.full_name}'
    )


def log_payment_confirmation(order, verified_by=None):
    """Log a payment confirmation."""
    logger.info(
        f'Payment confirmed - Order #{order.id} | '
        f'Amount: K{order.amount_paid} | '
        f'Verified by: {verified_by or "System"}'
    )