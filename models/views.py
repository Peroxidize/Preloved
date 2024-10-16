from django.http import JsonResponse
from django.shortcuts import render
from store.models import Slug, Item, Store
from .services import download_image, cascade_update_on_startup, query_database
from . import extractor
from homepage.views import HomePageController

# cascade_update_on_startup()
# Create your views here.

def get_similar_items(request):
    itemID = int(request.GET.get('item_id'))
    num = int(request.GET.get('num'))
    slug = Slug.objects.filter(itemID=itemID).first()
    link = HomePageController.generate_link(slug.slug)
    img = download_image(link)
    features = extractor.extract_features(img)
    itemsArr = query_database(features, n=num, not_equal_to=itemID)

    # Filter Items based on itemsArr
    similar_items = Item.objects.filter(itemID__in=itemsArr)

    # Prepare the data including the slug
    items_data = []
    for item in similar_items:
        slug = Slug.objects.filter(itemID=item.itemID).first()
        link = HomePageController.generate_link(slug.slug)
        items_data.append({
            'itemID': item.itemID,
            'name': item.name,
            'price': str(item.price),  # Convert Decimal to string for JSON serialization
            'image': link,
            'storeName': item.storeID.storeName
        })

    return JsonResponse({"items" : items_data})








