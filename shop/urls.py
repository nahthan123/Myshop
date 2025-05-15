from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views
from shop.views import (
    product_list, product_detail,
    add_to_cart, view_cart,
    update_cart, remove_from_cart,
    checkout, complete_order,
    register, user_account, order_detail,
    home,
)

urlpatterns = [
    path('', home, name='home'),
    path('products/', product_list, name='product_list'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', view_cart, name='view_cart'),
    path('cart/update/<int:product_id>/', update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('complete-order/', complete_order, name='complete_order'),

    # 🔐 Auth
    path('register/', register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Tài khoản người dùng
    path('account/', user_account, name='user_account'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
]
