from django.http import JsonResponse
from django.shortcuts import render
from store.models import Slug, Item
from .services import download_image, cascade_update_on_startup, query_database
from . import extractor

cascade_update_on_startup()
# Create your views here.

def get_similar_items(request):
    itemID = request.GET.get('item_id')
    item = Item.objects.get(pk=itemID)
    img = Slug.objects.filter(item=item).first()
    items = query_database(extractor.extract_features(img), not_equal_to=img.itemID)
    return JsonResponse({"items" : items})






