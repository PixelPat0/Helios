# ecom/context_processors.py

# CORRECT IMPORT: Notification is in payment.models
from payment.models import Notification

# The form is in store/forms.py
from payment.forms import NewsletterSubscriberForm 


def newsletter_form(request):
    """Adds the NewsletterSubscriberForm to the context, etc."""
    # Check for the flag set in payment views
    if getattr(request, 'disable_newsletter', False):
        return {
            'newsletter_form': None, 
        }
        
    return {
        'newsletter_form': NewsletterSubscriberForm(),
    }

def notifications(request): 
    """Adds the count AND the list of unread notifications for the logged-in user."""
    if request.user.is_authenticated:
        unread_notifications_list = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).order_by('-created_at')[:5] 
        
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        unread_notifications_list = []
        unread_count = 0
        
    return {
        'unread_notification_count': unread_count,
        'unread_notifications': unread_notifications_list,
    }