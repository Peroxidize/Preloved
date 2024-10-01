from django.urls import path
from .views import *

urlpatterns = [
    path('get_similar_items/', get_similar_items, name='index'),
]