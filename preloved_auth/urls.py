from django.contrib import admin

from django.urls import path, include
from .views import new_shop_user, csrf_token, loginAPI, logout_attempt, is_logged_in, shop_id_selfie, shop_id_two, shop_id_one, new_shop_owner, get_id_2, get_id_1, get_selfie

urlpatterns = [
    path('new_shop_user/', new_shop_user),
    path('csrf_token/', csrf_token),
    path('login/', loginAPI),
    path('logout/', logout_attempt),
    path('is_authenticated', is_logged_in),
    path('shop_id_one', shop_id_one),
    path('shop_id_two', shop_id_two),
    path('shop_id_selfie', shop_id_selfie),
    path('new_shop_owner', new_shop_owner),
    path('get_id_1', get_id_1),
    path('get_id_2', get_id_2),
    path('get_selfie', get_selfie)
]
