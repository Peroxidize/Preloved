from django.http import JsonResponse
from django.shortcuts import render
from store.views import return_not_auth, return_not_post, return_id_not_found
from .models import *
from preloved_auth.models import *
from store.models import *
# Create your views here.


class CollectionController:

    ## Important! Convenience method, do not include in documentation
    @staticmethod
    def get_shop_user(request):
        user = ShopUser.objects.get(userID=request.user)
        if user is None:
            return JsonResponse({'message': 'User is not a shop user'}, status=400)
        return user


    @staticmethod
    def create_collection(request):
        if request.method != 'POST':
            return return_not_post()
        user = CollectionController.get_shop_user(request)
        if not isinstance(user, ShopUser):
            return user
        collection_name = request.POST['collection_name']
        Collection.objects.create(name=collection_name, user=user)
        return JsonResponse({'message': 'success'}, status=201)



    @staticmethod
    def delete_collection(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        if request.method != 'POST':
            return return_not_post()
        user = CollectionController.get_shop_user(request)
        if not isinstance(user, ShopUser):
            return user
        
        collectionID = int(request.POST.get('collectionID'))
        if collectionID is None:
            return JsonResponse({'error': 'Invalid collection ID'}, status=400)
        collection = Collection.objects.get(id=collectionID)
        if collection is None:
            return JsonResponse({'error': 'Invalid collection ID'}, status=400)
        Collection.objects.get(user=user, id=collectionID).delete()
        return JsonResponse({'success': True}, status=200)


    @staticmethod
    def get_collections(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        user = CollectionController.get_shop_user(request)
        if not isinstance(user, ShopUser):
            return user
        collections = Collection.objects.filter(user=user, is_deleted=0)
        collection_list = []
        for collection in collections:
            instance = {}
            instance['id'] = collection.id
            instance['name'] = collection.name
            instance['created_at'] = collection.created_at
            collection_list.append(instance)
        return JsonResponse({'collections': collection_list}, status=200)

    @staticmethod
    def get_collection_items(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        user = CollectionController.get_shop_user(request)
        if not isinstance(user, ShopUser):
            return user

        collectionID = request.GET.get('collection_id')
        if collectionID is None:
            return JsonResponse({'error': 'Invalid collection ID'}, status=400)

        collection = Collection.objects.get(id=collectionID)

        set = CollectionItemUser.objects.filter(collection=collection, is_deleted=False)

        collection_list = []

        item_list = []

        for item in set:
            collection_list.append(item.item.itemID)

        for item in set:
            item = Item.objects.get(itemID=item.item.itemID)
            slug = Slug.objects.filter(itemID=item.itemID).first()
            if slug is None:
                continue
            link = CollectionController.generate_link(slug.slug)
            item_list.append({
                'itemID': item.itemID,
                'name': item.name,
                'price': str(item.price),  # Convert Decimal to string for JSON serialization
                'image': link,
                'storeName': item.storeID.storeName
            })

        returning_value = {'collectionID': collectionID, 'collectionName': collection.name, 'itemIDs': collection_list, 'itemInformation': item_list}
        return JsonResponse(returning_value, status=200)

    @staticmethod
    def get_similar_items_collection(request):
        from models.migrations.image_transformer import VGGFeatureExtractor, download_image
        from models.services import query_database, query_database_by_title
        extractor = VGGFeatureExtractor()

        recently_suggested = []
        recently_suggested_ids = set()  # To keep track of added item IDs
        collectionID = request.GET.get('collection_id')
        collection = Collection.objects.get(id=collectionID)
        if collectionID is None:
            return JsonResponse({'error': 'Invalid collection ID'}, status=400)

        collection_items = CollectionItemUser.objects.filter(collection=collection, is_deleted=False)
        if collection_items is None:
            return JsonResponse({'error': 'Empty set'}, status=400)

        itemID_list = []
        for item in collection_items:
            itemID_list.append(item.item.itemID)
        
        suggested_items = []
        for item in collection_items:
            slug = Slug.objects.filter(itemID=item.item).first()
            if slug:
                link = CollectionController.generate_link(slug.slug)
                img = download_image(link)
                features = extractor.extract_features(img)
                collection_query = query_database(features, 5, itemID_list)
                suggested_items.extend(collection_query)  # Use extend instead of append
        for itemID in suggested_items:
            if itemID not in recently_suggested_ids:
                item = Item.objects.get(itemID=itemID)
                recently_suggested.append(item)
                recently_suggested_ids.add(itemID)

        item_list = []
        seen_item_ids = set()  # Set to track item IDs that have been added
        for result_item_id in suggested_items:
            item = Item.objects.filter(itemID=result_item_id).first()
            slug2 = Slug.objects.filter(itemID=result_item_id).first()
    
            if not item or not slug2:  # Ensure item and slug exist
                continue
    
            if item.storeID.shopOwnerID.balance <= 0:
                continue

            # Check if item_id has already been added
            if item.itemID in seen_item_ids:
                continue

            map = {
                'item_id': item.itemID,
                'item_name': item.name,
                'item_description': item.description,
                'item_price': float(item.price),
                'size': item.size.sizeType,
                'is_feminine': item.isFeminine,
                'storeID': item.storeID.storeID,
                'storeName': item.storeID.storeName,
                'image': CollectionController.generate_link(slug2.slug),
            }

            item_list.append(map)
            seen_item_ids.add(item.itemID)  # Add item_id to the set

        return JsonResponse({'item_list': item_list}, status=200)

    @staticmethod
    def add_item_to_collection(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        if request.method != 'POST':
            return return_not_post()
        user = CollectionController.get_shop_user(request)
        if not isinstance(user, ShopUser):
            return user

        collectionID = request.POST.get('collectionID')
        if collectionID is None:
            return JsonResponse({'error': 'Invalid collection ID'}, status=400)
        collection = Collection.objects.get(id=collectionID)
        item = request.POST.get('itemID')
        item = Item.objects.get(itemID=item)
        if item is None:
            return JsonResponse({'error': 'Invalid item ID'}, status=400)
        
        try:
            temp = CollectionItemUser.objects.filter(user=user, collection=collection, item=item).first()
            if temp is not None:
                return JsonResponse({'error': 'Item is already in Collection'}, status=400)
        except Exception as e:
            pass
            
        CollectionItemUser.objects.create(user=user, collection=collection, item=item)
        return JsonResponse({'success': True}, status=200)


    @staticmethod
    def remove_item_from_collection(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        if request.method != 'POST':
            return return_not_post()
        user = CollectionController.get_shop_user(request)
        if not isinstance(user, ShopUser):
            return user

        collectionID = request.POST.get('collectionID')
        if collectionID is None:
            return JsonResponse({'error': 'Invalid collection ID'}, status=400)
        collection = Collection.objects.get(id=collectionID)
        item = request.POST.get('itemID')
        item = Item.objects.get(itemID=item)
        if item is None:
            return JsonResponse({'error': 'Invalid item ID'}, status=400)
        CollectionItemUser.objects.get(user=user, collection=collection, item=item).delete()
        return JsonResponse({'success': True}, status=200)

    @staticmethod
    def generate_link(slug):
        return "https://preloved.westus2.cloudapp.azure.com/media/"+ slug

    @staticmethod
    def rename_collection(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        if request.method != 'POST':
            return return_not_post()
        user = CollectionController.get_shop_user(request)
        if not isinstance(user, ShopUser):
            return user

        collectionID = request.POST.get('collectionID')
        if collectionID is None:
            return JsonResponse({'error': 'Invalid collection ID'}, status=400)

        # get the name
        new_name = request.POST.get('new_name')
        if new_name is None:
            return JsonResponse({'error': ''
                                          'Invalid new name'}, status=400)

        collection = Collection.objects.get(id=collectionID)
        collection.name = new_name
        collection.save()
        return JsonResponse({'success': True}, status=200)



