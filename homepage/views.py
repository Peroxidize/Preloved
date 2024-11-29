import weaviate
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.core.paginator import Paginator

from models.services import query_database, query_database_by_title
from preloved_collections.models import Collection, CollectionItemUser
from tickets.models import RecentlyBought, Ticket
from .models import *
# Create your views here.
from models.migrations.image_transformer import VGGFeatureExtractor, download_image
from models import title_model, central_model
from preloved_auth.models import *
from store.models import *
from preloved import preloved_secrets
import base64


class HomePageController:

    @staticmethod
    def homepage(request):
        page_number = request.GET.get('page', 1)
        items_per_page = 20  # Adjust this number as needed

        all_items = HomePageController.generate_iterative_homepage(request.user.id)
        paginator = Paginator(all_items, items_per_page)
        page_obj = paginator.get_page(page_number)

        return JsonResponse({
            'items': list(page_obj),
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
        })

    @staticmethod
    def generate_iterative_homepage(userID):
        items = Item.objects.filter(isTaken=0).order_by('?')
        recently_bought = RecentlyBought.objects.filter(userID=userID).order_by('-created').first()
        recently_query = []
        extractor = VGGFeatureExtractor()
        recently_suggested = []
        recently_suggested_ids = set()  # To keep track of added item IDs
        if recently_bought is not None:
            slug = Slug.objects.filter(itemID=recently_bought.itemID).first()
            link = HomePageController.generate_link(slug.slug)
            img = download_image(link)
            features = extractor.extract_features(img)
            recently_query = query_database(features, 10, not_equal_to=recently_bought.itemID.itemID)
            for itemID in recently_query:
                if itemID not in recently_suggested_ids:
                    item = Item.objects.get(itemID=itemID)
                    recently_suggested.append(item)
                    recently_suggested_ids.add(itemID)

        collections = Collection.objects.filter(user=userID)
        if len(collections) > 0:
            collection_suggested = []
            for collection in collections:
                collection_items = CollectionItemUser.objects.filter(collection=collection)
                if collection_items is not None:
                    for item in collection_items:
                        slug = Slug.objects.filter(itemID=item.item).first()
                        if slug:
                            link = HomePageController.generate_link(slug.slug)
                            img = download_image(link)
                            features = extractor.extract_features(img)
                            collection_query = query_database(features, 2)
                            collection_suggested.extend(collection_query)  # Use extend instead of append
            for itemID in collection_suggested:
                if itemID not in recently_suggested_ids:
                    item = Item.objects.get(itemID=itemID)
                    recently_suggested.append(item)
                    recently_suggested_ids.add(itemID)
        
        preferences, created = Preferences.objects.get_or_create(user=userID)
        tags = preferences.tags.all()
        for tag in tags:
            itemIDs = query_database_by_title(tag.name, 3)
            for itemID in itemIDs:
                if itemID not in recently_suggested_ids:
                    item = Item.objects.get(itemID=itemID)
                    recently_suggested.append(item)
                    recently_suggested_ids.add(itemID)

        # Add items not in recently_suggested to recently_suggested
        for item in items:
            if item.itemID not in recently_suggested_ids:
                recently_suggested.append(item)
                recently_suggested_ids.add(item.itemID)

        item_list = []
        for item in recently_suggested:
            if item.storeID.shopOwnerID.balance <= 0:
                continue
            map = {}
            map['item_id'] = item.itemID
            map['item_name'] = item.name
            map['item_description'] = item.description
            map['item_price'] = float(item.price)
            map['size'] = item.size.sizeType
            map['is_feminine'] = item.isFeminine
            map['storeID'] = item.storeID.storeID
            map['storeName'] = item.storeID.storeName
            images = []
            map['images'] = images
            image_slugs = Slug.objects.filter(itemID=item, isDeleted=0)
            for slug in image_slugs:
                images.append({'link': HomePageController.generate_link(slug.slug), 'slugID': slug.slugID})
            item_list.append(map)

        return item_list

    @staticmethod
    def generate_link(slug):
        return "https://preloved.westus2.cloudapp.azure.com/media/"+ slug

    @staticmethod
    def search(request):
        params = request.GET.get('q')
        # Query the collection
        results = title_model.query(
            query_texts=[params],
            n_results=20
        )
        # Extract item IDs from the results
        item_ids = [metadata['item_id'] for metadata in results['metadatas'][0]]
        query_result = []
        for itemID in item_ids:
            item = Item.objects.get(itemID=itemID)
            slug = Slug.objects.filter(itemID=item.itemID).first()
            if slug is None:
                continue
            link = HomePageController.generate_link(slug.slug)
            query_result.append({
                'itemID': item.itemID,
                'name': item.name,
                'price': str(item.price),  # Convert Decimal to string for JSON serialization
                'image': link,
                'storeName': item.storeID.storeName
            })
        # Return the results as JSON
        return JsonResponse({'results': query_result})

    @staticmethod
    def img_search(request):
        from store.views import return_not_post
        if request.method != 'POST':
            return return_not_post()

        params = request.FILES.get('photo')
        extractor = VGGFeatureExtractor()
        # Extract features from the uploaded image
        features = extractor.extract_features(params.read())

        # Query the central_model collection
        results = central_model.query(
            query_embeddings=[features.tolist()],
            n_results=20
        )

        # Extract item IDs from the results
        item_ids = [metadata['item_id'] for metadata in results['metadatas'][0]]

        # Prepare the query result
        query_result = []
        for itemID in item_ids:
            item = Item.objects.get(itemID=itemID)
            slug = Slug.objects.filter(itemID=item.itemID).first()
            if slug is None:
                continue
            link = HomePageController.generate_link(slug.slug)
            query_result.append({
                'itemID': item.itemID,
                'name': item.name,
                'price': str(item.price),  # Convert Decimal to string for JSON serialization
                'image': link,
                'storeName': item.storeID.storeName
            })

        # Return the results as JSON
        return JsonResponse({'results': query_result})


class CartController:

    @staticmethod
    def add_to_cart(request):
        from store.views import return_not_auth, return_not_post
        if not request.user.is_authenticated:
            return return_not_auth()
        if request.method != 'POST':
            return return_not_post()
        item = request.POST.get('itemID')
        item = Item.objects.get(itemID=item)
        tix = Ticket.objects.filter(userID_id=request.user.id, itemID=item)
        for ticket in tix:
            if ticket.status.level <= 2:
                return JsonResponse({"error": "Cannot add item to card. Pending ticket already exists."}, status=400)
        Cart(user=request.user, item=item).save()
        return JsonResponse({'success': True})

    @staticmethod
    def remove_from_cart(request):
        from store.views import return_not_auth, return_not_post
        if not request.user.is_authenticated:
            return return_not_auth()
        if request.method != 'POST':
            return return_not_post()
        item = request.POST.get('itemID')
        item = Item.objects.filter(itemID=item).first()
        item = Cart.objects.filter(user=request.user, item=item)
        if item is None:
            return JsonResponse({'success': False})
        item.delete()
        return JsonResponse({'success': True})

    @staticmethod
    def get_cart_items(request):
        from store.views import return_not_auth
        if not request.user.is_authenticated:
            return return_not_auth
        cartItems = Cart.objects.filter(user=request.user)
        shoppingCart = []
        for item in cartItems:
            firstItem: Slug = Slug.objects.filter(isDeleted=0, itemID=item.item).first()
            shoppingCart.append({
                'itemID': item.item.itemID,
                'price': item.item.price,
                'storeName': item.item.storeID.storeName,
                'storeID': item.item.storeID.storeID,
                'size': item.item.size.sizeType,
                'thumbnail': "https://preloved.westus2.cloudapp.azure.com/media/" + firstItem.slug
            })
        return JsonResponse({'cart': shoppingCart})

    @staticmethod
    def purchase_all(request):
        from store.views import return_not_auth
        if not request.user.is_authenticated:
            return return_not_auth()
        items = Cart.objects.all()
        for item in items:
            try:
                Ticket.objects.create(userID=request.user, storeID=item.item.storeID, itemID=item.item,
                                      expected_seller_fulfillment=timezone.now() + timezone.timedelta(5)).save()
                item.delete()
            except Exception as e:
                print('WHY? ', e)

        return JsonResponse({'success': True})
