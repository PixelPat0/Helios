# payment/email_utils.py

import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model

# Import project-specific models/helpers
from .models import Seller # Assuming Seller is in the same app's models.py
from .utils import create_notification # Assuming this is your notification creation helper

logger = logging.getLogger(__name__)
User = get_user_model()

# --- Helper Functions for Email Content ---

def _render_email_content(template_html, template_txt, context):
    """
    Renders HTML and Txt templates, falling back to stripping HTML tags 
    for the text version if the text template is missing.
    """
    html_message = render_to_string(template_html, context)
    
    try:
        text_message = render_to_string(template_txt, context)
    except Exception:
        # Fallback: create plain text from HTML
        text_message = strip_tags(html_message)
        
    return html_message, text_message

# ======================================================================
# A. GENERIC EMAIL UTILITY
# ======================================================================

def send_generic_email(subject, template_name, context, recipient_list):
    """
    Sends a generic HTML email notification.
    
    :param subject: Email subject line.
    :param template_name: Base name for templates (e.g., 'welcome' will look for 'welcome.html').
    :param context: Dictionary for template rendering.
    :param recipient_list: List of email addresses.
    :returns: True on success, False otherwise.
    """
    if not recipient_list:
        logger.warning("Attempted to send generic email with no recipients: %s", subject)
        return False

    template_html = f'payment/emails/{template_name}.html'
    template_txt = f'payment/emails/{template_name}.txt'

    try:
        html_message, text_message = _render_email_content(template_html, template_txt, context)
        
        send_mail(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Sent generic email: '%s' to %s", subject, recipient_list)
        return True
    
    except Exception:
        # Use logger.exception to log the full traceback automatically
        logger.exception("Failed to send generic email: '%s' to %s", subject, recipient_list)
        return False

# ======================================================================
# B. ORDER SPECIFIC NOTIFICATIONS
# ======================================================================

def _group_items_by_seller(items):
    """Groups OrderItem list into a dictionary keyed by the Seller object."""
    sellers_items = {}
    for item in items:
        # Determine the seller, preferring OrderItem.seller, then Product.seller
        seller = getattr(item, 'seller', None) or getattr(getattr(item, 'product', None), 'seller', None)
        sellers_items.setdefault(seller, []).append(item)
    return sellers_items

def send_order_notifications(order, items):
    """
    Handles robust email and in-app notification for a new order.
    Targets: Admin(s), Seller(s), and Customer.
    """
    order_id = getattr(order, 'id', 'unknown')
    
    try:
        sellers_items = _group_items_by_seller(items)

        # 1. ADMIN NOTIFICATIONS
        _send_admin_notifications(order, items, sellers_items)

        # 2. SELLER NOTIFICATIONS
        for seller_obj, items_list in sellers_items.items():
            _send_seller_notifications(order, seller_obj, items_list)

        # 3. CUSTOMER NOTIFICATION
        _send_customer_confirmation(order, items)

    except Exception:
        logger.exception("Unexpected failure during send_order_notifications for order #%s", order_id)

# --- Internal Order Notification Helpers ---

def _send_admin_notifications(order, items, sellers_items):
    """Sends email and in-app notifications to admins."""
    order_id = getattr(order, 'id', 'unknown')
    
    # 1. Prepare Context
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

    # 2. Determine Recipients
    admin_recipients = []
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    if admin_email:
        admin_recipients.append(admin_email)
    
    # Always include all superusers as fallback for in-app and potentially email
    superuser_users = list(User.objects.filter(is_superuser=True))
    admin_recipients.extend(list(u.email for u in superuser_users if u.email and u.email not in admin_recipients))
    admin_recipients = list(set(admin_recipients)) # Deduplicate recipients

    # 3. Send Email
    if admin_recipients:
        try:
            html_message, text_message = _render_email_content(
                'payment/emails/admin_order_notification.html',
                'payment/emails/admin_order_notification.txt',
                admin_context
            )
            
            subject = f'New Order #{order_id} Received - Action Required'
            msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, admin_recipients)
            msg.attach_alternative(html_message, "text/html")
            msg.send(fail_silently=False)
            logger.info("Admin order email sent for order %s to %s", order_id, admin_recipients)
        except Exception:
            logger.exception("Failed to send admin order email for order %s", order_id)
    else:
        logger.warning("No admin recipients configured for order %s.", order_id)

    # 4. Create In-App Notification (to all superusers)
    try:
        for u in superuser_users:
            create_notification(user=u, message=f"New customer order #{order_id} placed. Review and process.", order_id=order_id)
    except Exception:
        logger.exception("Failed to create admin notification for order %s", order_id)

def _send_seller_notifications(order, seller_obj, items_list):
    """Sends email and in-app notifications to an individual seller."""
    order_id = getattr(order, 'id', 'unknown')
    seller_name = getattr(seller_obj, 'username', getattr(seller_obj, 'name', 'Unknown Seller'))
    
    # 1. Determine Contact Info
    seller_user = getattr(seller_obj, 'user', None) # Linked Django User
    seller_email = getattr(seller_obj, 'email', None) or getattr(seller_user, 'email', None)

    # 2. Prepare Context
    seller_context = {
        'order': order,
        'seller': seller_obj,
        'items': items_list,
        'seller_name': seller_name,
    }

    # 3. Send Email
    if seller_email:
        try:
            html_message, text_message = _render_email_content(
                'payment/emails/seller_order_notification.html',
                'payment/emails/seller_order_notification.txt',
                seller_context
            )
            
            subject = f'New Order #{order_id} - Items to Fulfill'
            msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [seller_email])
            msg.attach_alternative(html_message, "text/html")
            msg.send(fail_silently=False)
            logger.info("Sent seller email to %s for order %s", seller_email, order_id)
        except Exception:
            logger.exception("Failed to send seller email to %s for order %s", seller_email, order_id)
    
    # 4. Create In-App Notification (Targeting the linked user or admin fallback)
    try:
        if seller_user:
            # Send notification to the linked Django User
            create_notification(
                user=seller_user,
                message=f"New customer order #{order_id} includes items from your store. ({len(items_list)} unique item(s))",
                order_id=order_id
            )
        elif not seller_email:
            # Fallback: Notify admins if seller is unreachable by email AND lacks a linked user
            for u in User.objects.filter(is_superuser=True):
                create_notification(
                    user=u,
                    message=f"CRITICAL: Order #{order_id} has items for seller '{seller_name}' but lacks contact info (no linked user/email).",
                    order_id=order_id
                )
    except Exception:
        logger.exception("Failed to create seller in-app notification for order %s and seller %s", order_id, seller_name)

def _send_customer_confirmation(order, items):
    """Sends the order confirmation email to the customer."""
    order_id = getattr(order, 'id', 'unknown')
    customer_email = getattr(order, 'email', None) or (getattr(getattr(order, 'user', None), 'email', None))

    if customer_email:
        cust_context = {'order': order, 'items': items}
        try:
            html_message, text_message = _render_email_content(
                'payment/emails/customer_order.html',
                'payment/emails/customer_order.txt',
                cust_context
            )
            
            subject = f'Order Confirmation #{order_id} - HELIOS'
            msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [customer_email])
            msg.attach_alternative(html_message, "text/html")
            msg.send(fail_silently=False)
            logger.info("Sent customer confirmation to %s for order %s", customer_email, order_id)
        except Exception:
            logger.exception("Failed to send customer confirmation to %s for order %s", customer_email, order_id)
    else:
        logger.warning("No customer email available for order %s; skipping customer email.", order_id)