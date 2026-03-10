from django.urls import path
from . import views

urlpatterns = [
    # Home Page is now Solutions
    path('', views.solutions_view, name='home'),
    
    # Store Routes
    path('store/', views.store_home, name='store'),  # Store home
    path('store/category/<str:foo>/', views.category, name='category'),
    path('store/categories/', views.category_summary, name='category_summary'),
    path('store/product/<int:pk>/', views.product_view, name='product'),
    path('store/search/', views.search, name='search'),
    
    # Keep existing URLs for backward compatibility (optional)
    path('category/<str:foo>/', views.category, name='category_old'),
    path('categories/', views.category_summary, name='category_summary_old'),
    path('product/<int:pk>/', views.product_view, name='product_old'),
    
    # Authentication & User Management
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('update-password/', views.update_password, name='update_password'),
    path('update-user/', views.update_user, name='update_user'),
    path('update-info/', views.update_info, name='update_info'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    
    # Content Pages
    path('about/', views.about, name='about'),
    path('solutions/', views.solutions_view, name='solutions'),
    path('donate/', views.donation_page_view, name='donation_page'),
    
    # Seller/Profile
    path('seller/<int:pk>/', views.seller_profile_public, name='seller_profile_public'),
    
    # Contact (SIMPLE MVP VERSION)
    path('contact/', views.contact, name='contact'),  # Just one name
    
    # Newsletter
    path('subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    
    # Notifications
    path('notifications/', views.notifications_list_view, name='notifications_list'),
    path('notifications/open/<int:pk>/', views.notification_open, name='notification_open'),
    path('notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    
    # Quotes
    path('request-quote/', views.request_quote, name='request_quote'),
    path('confirm-quote/', views.confirm_quote_request, name='confirm_quote_request'),
    path('quote-details/<int:quote_request_id>/', views.quote_request_details, name='quote_request_details'),
    path('quote-export-pdf/<int:quote_request_id>/', views.export_quote_request_pdf, name='export_quote_pdf'),
    path('my-quotes/', views.quote_request_list, name='quote_request_list'),
]