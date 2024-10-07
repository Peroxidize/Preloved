from django.http import JsonResponse
from django.shortcuts import render
from store.models import Slug, Item
from .services import download_image, cascade_update_on_startup, query_database
from . import extractor
from homepage.views import HomePageController

# cascade_update_on_startup()
# Create your views here.

def get_similar_items(request):
    itemID = request.GET.get('item_id')
    num = request.GET.get('num')
    slug = Slug.objects.filter(itemID=itemID).first()
    imgURL = HomePageController.generate_link(slug.slug)
    img = download_image(imgURL)
    features = extractor.extract_features(img)
    items = query_database(features, n=num, not_equal_to=itemID)
    return JsonResponse({"items" : items})








