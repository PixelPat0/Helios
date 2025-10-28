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

logger = logging.getLogger(__name__)

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
    Send email notifications and create internal database notifications 
    for the admin and relevant sellers about a new order.
    """
    User = get_user_model() # Define User model for clear Admin lookup
    
    try:
        # Calculate total commission (Used for Admin Context)
        total_commission = sum(item.commission_amount for item in items)

        # Group items by seller USER object (THIS IS THE KEY FIX)
        sellers_items = {}
        for item in items:
            # 1. Get the custom Seller object from the Product
            if hasattr(item.product, 'seller') and item.product.seller:
                seller_profile = item.product.seller
            else:
                print(f"Warning: Product {item.product.name} missing seller profile.")
                continue 
            
            # 2. Get the Django User object from the Seller profile
            try:
                seller_user = seller_profile.user # Assumes SellerProfile has a ForeignKey to User named 'user'
            except AttributeError:
                print(f"Warning: Seller profile for product {item.product.name} missing linked User object.")
                continue

            # Use the User object for grouping
            if seller_user not in sellers_items:
                sellers_items[seller_user] = []
            sellers_items[seller_user].append(item)

        # ----------------------------------------------------------------------
        # 1. ADMIN EMAIL NOTIFICATION (No change needed here, just the variable names)
        # ----------------------------------------------------------------------
        
        # We need a list of User objects for the admin context breakdown
        sellers_breakdown_list = [
            {
                'seller_name': seller_user.username, # Now guaranteed to be a User object
                'items': items_list,
                'total': sum(item.price * item.quantity for item in items_list),
                'commission': sum(item.commission_amount for item in items_list)
            }
            for seller_user, items_list in sellers_items.items()
        ]
        
        admin_context = {
            'order': order,
            'items': items,
            'total_commission': total_commission,
            'sellers_breakdown': sellers_breakdown_list
        }
        
        admin_message = render_to_string(
            'payment/emails/admin_order_notification.html', 
            admin_context
        )
        
        # Send email to admin (use HTML + plain fallback, safe send)
        try:
            admin_plain = ''
            try:
                admin_plain = render_to_string('payment/emails/admin_order_notification.txt', admin_context)
            except Exception:
                admin_plain = strip_tags(admin_message)

            subject = f'New Order #{order.id} Received - Action Required'
            msg = EmailMultiAlternatives(subject, admin_plain, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_EMAIL])
            msg.attach_alternative(admin_message, "text/html")
            msg.send(fail_silently=False)
        except Exception as e:
            logger.exception("Failed to send admin order email for order %s: %s", getattr(order, 'id', 'unknown'), e)
        
        # ----------------------------------------------------------------------
        # 2. CREATE INTERNAL NOTIFICATIONS
        # ----------------------------------------------------------------------
        
        # A. Notification for Admin
        try:
            # Look up the admin User object by the ADMIN_EMAIL setting
            admin_user = User.objects.get(email=settings.ADMIN_EMAIL)
            # REPLACED Notification.objects.create with helper function
            create_notification(
                user=admin_user,
                message=f"NEW ORDER #{order.id}: Received a total order of ZMK {order.amount_paid:.2f}. Click to view details.",
                order_id=order.id
            )
        except User.DoesNotExist:
            print(f"Warning: Admin user not found with email {settings.ADMIN_EMAIL}. Cannot create notification.")
        except Exception as e:
            print(f"Warning: Could not create Admin notification. Error: {e}")
        
        
        # 3. SELLER EMAIL AND DB NOTIFICATIONS
        for seller_user, seller_items in sellers_items.items():
            seller_total = sum(item.price * item.quantity for item in seller_items)
            seller_commission = sum(item.commission_amount for item in seller_items)

            # Determine seller email safely:
            seller_email = None
            # Product.seller is the Seller model instance; use its business_email if present
            seller_profile = getattr(seller_items[0].product, 'seller', None)
            if seller_profile:
                # Prefer business_email field on Seller model
                seller_email = getattr(seller_profile, 'business_email', None)

            # fallback to Django user email
            if not seller_email:
                seller_email = getattr(seller_user, 'email', None)

            # If still no email, skip sending email (but still create DB notification)
            if not seller_email:
                print(f"Warning: No email available for seller {getattr(seller_user,'username',seller_user)}; skipping email send.")
            else:
                seller_context = {
                    'order_id': order.id,
                    'items': seller_items,
                    'total_amount': seller_total,
                    'commission': seller_commission,
                    'net_amount': seller_total - seller_commission,
                    'customer_name': order.full_name,
                    'customer_address': order.shipping_address,
                    'customer_email': order.email,
                }

                try:
                    seller_message = render_to_string(
                        'payment/emails/seller_order_notification.html',
                        seller_context
                    )
                except Exception as e:
                    print(f"Template error rendering seller email: {e}")
                    seller_message = None

                if seller_message and settings.DEBUG:
                    print(f"DEBUG: Would send email to seller {seller_user.username} at {seller_email}")
                elif seller_message:
                    try:
                        seller_plain = ''
                        try:
                            seller_plain = render_to_string('payment/emails/seller_order_notification.txt', seller_context)
                        except Exception:
                            seller_plain = strip_tags(seller_message)

                        subject = f'New Order #{order.id} Received'
                        seller_email_msg = EmailMultiAlternatives(subject, seller_plain, settings.DEFAULT_FROM_EMAIL, [seller_email])
                        seller_email_msg.attach_alternative(seller_message, "text/html")
                        seller_email_msg.send(fail_silently=False)
                        logger.info("Sent seller email to %s for order %s", seller_email, order.id)
                    except Exception as e:
                        logger.exception("Failed to send seller email to %s for order %s: %s", seller_email, getattr(order, 'id', 'unknown'), e)
# ...existing code...
            # Create DB Notification for seller_user
            try:
                # REPLACED Notification.objects.create with helper function
                create_notification(
                    user=seller_user,
                    message=f"New Order #{order.id}! Items totalling ZMK {seller_total:.2f} from your store. Fulfill now.",
                    order_id=order.id
                )
            except Exception as e:
                print(f"Warning: Could not create notification for seller {seller_user.username}. Error: {e}")


    except Exception as e:
        print(f"Error sending order notifications: {e}")
        if settings.DEBUG:
            raise