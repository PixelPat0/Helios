# payment/email_utils.py (or where this code lives)

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
# NOTE: Removed Notification import as it will now be imported from utils
from .models import Seller
from .utils import create_notification # <-- NEW: Import the helper function
from django.contrib.auth import get_user_model # Import for Admin User lookup

# NEW imports
import logging
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

# ----------------------------------------------------------------------
# A. GENERIC UTILITY FOR SELLER COMMUNICATIONS (RENAMED to send_generic_email)
# ----------------------------------------------------------------------

def send_generic_email(subject, template_name, context, recipient_list):
    """
    Sends a generic HTML email notification for updates (e.g., Welcome, Policy, Report).
    """
    try:
        html_message = render_to_string(template_name, context)
        message = html_message 
        from_email = settings.DEFAULT_FROM_EMAIL
        
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    
    except Exception as e:
        print(f"Error sending generic email to {recipient_list}: {e}")
        return False

# ----------------------------------------------------------------------
# B. ORDER SPECIFIC NOTIFICATIONS (Updated to use create_notification helper)
# ----------------------------------------------------------------------

def send_order_notifications(order, items):
    """
    Robust email + in-app notification sender for new orders.
    - Sends admin email (to settings.ADMIN_EMAIL or superusers)
    - Sends seller email per seller (if seller has an email) or creates a notification
    - Sends customer confirmation if order.email or order.user.email exists
    - Uses EmailMultiAlternatives with plain-text fallback
    """
    try:
        # Group order items by seller (seller may be OrderItem.seller or product.seller)
        sellers_items = {}
        for item in items:
            seller = getattr(item, 'seller', None) or getattr(getattr(item, 'product', None), 'seller', None)
            if seller is None:
                # fallback to product.seller_user or similar if your model differs
                sellers_items.setdefault(None, []).append(item)
            else:
                sellers_items.setdefault(seller, []).append(item)

        # Prepare admin context and send admin email
        total_commission = sum((item.price * item.quantity * item.commission_rate) for item in items)
        admin_context = {
            'order': order,
            'items': items,
            'sellers_breakdown': [
                {
                    'seller_name': getattr(seller, 'username', getattr(seller, 'name', str(seller))),
                    'items': items_list,
                    'total': sum(item.price * item.quantity for item in items_list),
                    'commission': sum(item.price * item.quantity * item.commission_rate for item in items_list)
                }
                for seller, items_list in sellers_items.items() if seller is not None
            ],
            'total_commission': total_commission,
        }

        admin_html = render_to_string('payment/emails/admin_order_notification.html', admin_context)
        try:
            admin_txt = render_to_string('payment/emails/admin_order_notification.txt', admin_context)
        except Exception:
            admin_txt = strip_tags(admin_html)

        admin_recipients = []
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if admin_email:
            admin_recipients = [admin_email]
        else:
            # fallback to all superusers' emails
            admin_recipients = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))

        if admin_recipients:
            try:
                subject = f'New Order #{order.id} Received - Action Required'
                msg = EmailMultiAlternatives(subject, admin_txt, settings.DEFAULT_FROM_EMAIL, admin_recipients)
                msg.attach_alternative(admin_html, "text/html")
                msg.send(fail_silently=False)
                logger.info("Admin order email sent for order %s to %s", order.id, admin_recipients)
            except Exception as e:
                logger.exception("Failed to send admin order email for order %s: %s", getattr(order, 'id', 'unknown'), e)
        else:
            logger.warning("No admin recipients configured (ADMIN_EMAIL or superusers missing).")

        # Create admin in-app notification (optional)
        try:
            if admin_email:
                admin_user = User.objects.filter(email=admin_email, is_superuser=True).first()
                if admin_user:
                    create_notification(user=admin_user, message=f"New order #{order.id} placed.", order=order)
            else:
                for u in User.objects.filter(is_superuser=True):
                    create_notification(user=u, message=f"New order #{order.id} placed.", order=order)
        except Exception:
            logger.exception("Failed to create admin notification for order %s", getattr(order, 'id', 'unknown'))

        # Send seller emails / create notifications
        for seller, items_list in sellers_items.items():
            seller_name = getattr(seller, 'username', getattr(seller, 'name', str(seller))) if seller else "Unknown Seller"
            seller_email = None
            # try common places for seller email
            if seller is not None:
                seller_email = getattr(seller, 'email', None) or getattr(getattr(seller, 'user', None), 'email', None)

            seller_context = {
                'order': order,
                'seller': seller,
                'items': items_list,
                'seller_name': seller_name,
            }

            seller_html = render_to_string('payment/emails/seller_order_notification.html', seller_context)
            try:
                seller_txt = render_to_string('payment/emails/seller_order_notification.txt', seller_context)
            except Exception:
                seller_txt = strip_tags(seller_html)

            if seller_email:
                try:
                    subject = f'New Order #{order.id} - Items to Fulfill'
                    msg = EmailMultiAlternatives(subject, seller_txt, settings.DEFAULT_FROM_EMAIL, [seller_email])
                    msg.attach_alternative(seller_html, "text/html")
                    msg.send(fail_silently=False)
                    logger.info("Sent seller email to %s for order %s", seller_email, order.id)
                except Exception:
                    logger.exception("Failed to send seller email to %s for order %s", seller_email, getattr(order, 'id', 'unknown'))
            else:
                # Create internal notification for the seller (if mapped to a user) or admin fallback
                try:
                    if seller and getattr(seller, 'user', None):
                        create_notification(user=seller.user, message=f"New order #{order.id} contains your items.", order=order)
                    else:
                        # notify admins if seller has no email/user
                        for u in User.objects.filter(is_superuser=True):
                            create_notification(user=u, message=f"Order #{order.id} contains items for seller '{seller_name}' with no contact email.", order=order)
                except Exception:
                    logger.exception("Failed to create seller notification for order %s and seller %s", getattr(order, 'id', 'unknown'), seller_name)

        # Send customer confirmation email (if email available)
        customer_email = getattr(order, 'email', None) or (getattr(getattr(order, 'user', None), 'email', None))
        if customer_email:
            cust_context = {'order': order, 'items': items}
            cust_html = render_to_string('payment/emails/customer_order.html', cust_context)
            try:
                cust_txt = render_to_string('payment/emails/customer_order.txt', cust_context)
            except Exception:
                cust_txt = strip_tags(cust_html)

            try:
                subject = f'Order Confirmation #{order.id} - HELIOS'
                msg = EmailMultiAlternatives(subject, cust_txt, settings.DEFAULT_FROM_EMAIL, [customer_email])
                msg.attach_alternative(cust_html, "text/html")
                msg.send(fail_silently=False)
                logger.info("Sent customer confirmation to %s for order %s", customer_email, order.id)
            except Exception:
                logger.exception("Failed to send customer confirmation to %s for order %s", customer_email, getattr(order, 'id', 'unknown'))
        else:
            logger.warning("No customer email available for order %s; skipping customer email.", getattr(order, 'id', 'unknown'))

    except Exception as e:
        logger.exception("Unexpected error in send_order_notifications for order %s: %s", getattr(order, 'id', 'unknown'), e)