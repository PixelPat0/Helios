from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('login', views.login_user, name='login'),
    path('logout', views.logout_user, name='logout'),
    path('register', views.register_user, name='register'),
    path('update_password', views.update_password, name='update_password'),
    path('update_user', views.update_user, name='update_user'),
    path('update_info', views.update_info, name='update_info'),
    path('product/<int:pk>', views.product_view, name='product'),
    path('category/<str:foo>', views.category, name='category'),
    path('category_summary/', views.category_summary, name='category_summary'),
    path('search/', views.search, name='search'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('seller/<int:pk>/', views.seller_profile_public, name='seller_profile_public'),
    path('impact/', views.public_impact_view, name='public_impact'),
    path('donate/', views.donation_page_view, name='donation_page'),
    path('subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('notifications/', views.notifications_list_view, name='user_notifications_list'), # <-- RENAMED
    # path('notifications/read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'), # Optional detail view
]
