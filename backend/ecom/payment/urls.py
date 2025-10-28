# payment/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # admin dashboards
    path('payment_success/', views.payment_success, name='payment_success'),
    path('checkout/', views.checkout, name='checkout'),
    path('billing_info/', views.billing_info, name='billing_info'),
    path('process_order/', views.process_order, name='process_order'),
    path('shipped_dash/', views.shipped_dash, name='shipped_dash'),
    path('not_shipped_dash/', views.not_shipped_dash, name='not_shipped_dash'),
    path('orders/<int:pk>/', views.orders, name='orders'),
    path('export_order/<int:order_id>/', views.export_order_details, name='export_order_details'),

    # Seller flow
    path('seller/signup/', views.seller_signup, name='seller_signup'),
    path('seller/login/', views.seller_login, name='seller_login'),
    path('seller/logout/', views.seller_logout, name='seller_logout'),
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/profile/', views.seller_profile_view, name='seller_profile'),
    #path('seller/order/<int:order_id>/cancel/', views.cancel_order, name='seller_cancel_order'),
    path('seller/order/<int:order_id>/', views.seller_order_detail, name='seller_order_detail'),

    # Seller product CRUD
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('products/delete/<int:pk>/', views.product_delete, name='product_delete'),
    
    # seller order detail and update
    
    path('dashboard/update_order_status/<int:pk>/', views.update_order_status, name='update_order_status'),

    # notifications
    path('notifications/<int:notif_id>/open/', views.notification_redirect_view, name='notification_open'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/mark_all_read/', views.mark_all_notifications_read, name='mark_all_notifications_read'), 
]
