from django.urls import path
from .views import *

urlpatterns = [
    path('long_poll_messages', long_poll_messages),
    path('send_message', send_message),
    path('fetch_all_messages', fetch_all_messages),
    path('fetch_chat_history_user', fetch_chat_history_user),
    path('fetch_chat_history_seller', fetch_chat_history_seller),
]
