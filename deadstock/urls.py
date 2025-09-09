from django.contrib import admin
from django.urls import path, include
from marketplace import views
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),

    # product pages
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/add/', views.product_create, name='product_create'),
    path('product/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('product/<int:pk>/buy/', views.order_create, name='order_create'),

    # seller signup & dashboard
    path('signup/', views.seller_signup, name='seller_signup'),
    path('seller/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    
    



    # authentication (login/logout/password reset)
    path('accounts/', include('django.contrib.auth.urls')),

    # optional: redirect /accounts/profile/ → homepage
    path('accounts/profile/', lambda request: redirect('product_list')),
]

# serve media files (product images) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
