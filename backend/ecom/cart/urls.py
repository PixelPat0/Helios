from django.urls import path
from . import views
from .views import cart_add

urlpatterns = [
    # URL pattern for the cart summary page
    path('', views.cart_summary, name='cart_summary'),

    # URL pattern for adding a product to the cart
    path('cart/add/', cart_add, name='cart_add'),

    # URL pattern for deleting a product from the cart (to be implemented)
    path('cart/delete/', views.cart_delete, name='cart_delete'),

    # URL pattern for updating the cart (to be implemented)
    path('cart/update/', views.cart_update, name='cart_update'),
]