import weaviate
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from tickets.models import Ticket
from .models import *
# Create your views here.

from preloved_auth.models import *
from store.models import *
from store.views import return_not_auth, return_not_post, return_id_not_found
from preloved import preloved_secrets
import base64


class HomePageController:

    @staticmethod
    def homepage(request):
        if request.session.get('items') is None:
            request.session['items'] = []
        if len(request.session.get('items')) <= 5:
            request.session['items'] = HomePageController.generate_iterative_homepage()
        item: list = request.session['items']
        items = []
        try:
            for i in range(50):
                items.append(item.pop())
        except IndexError:
            pass
        return JsonResponse({'items': items})

    @staticmethod
    def generate_iterative_homepage():
        items = Item.objects.filter(isTaken=0).order_by('?')
        item_list = []
        for item in items:
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
        client = weaviate.connect_to_custom(
            http_host="34.87.112.226",
            http_port=8080,
            http_secure=False,
            grpc_host="34.87.112.226",
            grpc_port=50051,
            grpc_secure=False,
        )
        results = None
        try:
            items = client.collections.get("ItemMM")
            results = items.query.near_text(
                query=params,
                distance=0.6,
                return_properties=["itemId", "name"]
            )
        finally:
            client.close()
        query_result = []
        itemIDs = []
        for result in results.objects:
            if result.properties["itemId"] in itemIDs:
                continue
            query_result.append({
                'itemID': result.properties["itemId"],
                'name': result.properties["name"]
            })
            itemIDs.append(result.properties["itemId"])
        return JsonResponse({'results': query_result})

    @staticmethod
    def img_search(request):
        if request.method != 'POST':
            return return_not_post()

        params = request.FILES.get('photo')
        client = weaviate.connect_to_custom(
            http_host="34.87.112.226",
            http_port=8080,
            http_secure=False,
            grpc_host="34.87.112.226",
            grpc_port=50051,
            grpc_secure=False,
        )
        results = None
        try:
            items = client.collections.get("ItemMM")
            photo_data = params.read()
            encoded = base64.b64encode(photo_data).decode('utf-8')
            results = items.query.near_image(
                near_image=encoded,
                distance=0.6,
                return_properties=["itemId", "name"]
            )
        finally:
            client.close()
        query_result = []
        itemIDs = []
        for result in results.objects:
            if result.properties["itemId"] in itemIDs:
                continue
            query_result.append({
                'itemID': result.properties["itemId"],
                'name': result.properties["name"]
            })
            itemIDs.append(result.properties["itemId"])
        return JsonResponse({'results': query_result})


class CartController:

    @staticmethod
    def add_to_cart(request):
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
