from django.contrib import admin
from django.urls import path, include
from . import settings
from django.conf.urls.static import static
from store import views as store_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('cart/', include('cart.urls')),
    path('payment/', include('payment.urls')),

    # explicit aliases (optional)
    path('about/', store_views.about, name='about'),
    path('public-impact/', store_views.about, name='public_impact'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
