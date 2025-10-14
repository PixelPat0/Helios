from .models import Notification
from django.utils import timezone

def create_notification(user, message, order_id=None):
    """
    Simple helper to create a Notification. Keeps code DRY.
    """
    return Notification.objects.create(
        user=user,
        message=message,
        order_id=order_id,
        is_read=False,
        created_at=timezone.now()
    )