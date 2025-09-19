from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal

def send_order_notifications(order, items):
    """Send email notifications to admin and sellers"""
    try:
        # Calculate total commission
        total_commission = sum(item.commission_amount for item in items)

        # Group items by seller for admin reference
        sellers_items = {}
        for item in items:
            if item.seller:
                if item.seller not in sellers_items:
                    sellers_items[item.seller] = []
                sellers_items[item.seller].append(item)

        # Prepare comprehensive admin notification
        admin_context = {
            'order': order,
            'items': items,
            'total_commission': total_commission,
            'sellers_breakdown': [
                {
                    'seller_name': seller.get_full_name() or seller.username,
                    'items': items_list,
                    'total': sum(item.price * item.quantity for item in items_list),
                    'commission': sum(item.commission_amount for item in items_list)
                }
                for seller, items_list in sellers_items.items()
            ]
        }
        
        admin_message = render_to_string(
            'payment/email/admin_order_notification.html', 
            admin_context
        )
        
        # Send only to admin
        send_mail(
            subject=f'New Order #{order.id} Received - Action Required',
            message=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            html_message=admin_message,
            fail_silently=False
        )

        # Send notifications to sellers
        for seller, seller_items in sellers_items.items():
            seller_total = sum(item.price * item.quantity for item in seller_items)
            seller_commission = sum(item.commission_amount for item in seller_items)

            # Get seller's business email
            seller_email = seller.profile.get_business_email()

            seller_context = {
                'order_id': order.id,
                'items': seller_items,
                'total_amount': seller_total,
                'commission': seller_commission,
                'net_amount': seller_total - seller_commission
            }

            seller_message = render_to_string(
                'payment/email/seller_order_notification.html',
                seller_context
            )

            # Send to seller (in development, this goes to test email)
            if settings.DEBUG:
                print(f"Would send email to seller {seller.username} at {seller_email}")
                print(f"Email content: {seller_message}")
            else:
                send_mail(
                    subject=f'New Order #{order.id} Received',
                    message=seller_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[seller_email],
                    html_message=seller_message,
                    fail_silently=False
                )

    except Exception as e:
        print(f"Error sending notifications: {e}")
        if settings.DEBUG:
            raise  # Re-raise the exception in development