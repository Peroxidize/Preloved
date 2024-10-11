import random
import json
from django.urls import reverse
from functools import wraps
from urllib import request
import os
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from models.migrations.image_transformer import VGGFeatureExtractor
from models.services import query_database_by_image
from .models import *
from preloved_auth.models import ShopOwner, Location
from storage.views import StorageWorker
import torch 
import pandas as pd
from PIL import Image
from torch import nn, optim
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights
from django.core.files.uploadedfile import InMemoryUploadedFile
import base64
import weaviate
from weaviate.util import generate_uuid5
"""
df = pd.read_csv("~/preloved/store/empty-dataset.csv")

model = mobilenet_v3_large()
weights = MobileNet_V3_Large_Weights.DEFAULT
preprocess = weights.transforms()

# Freeze the feature extractor layers
for param in model.parameters():
    param.requires_grad = False

# Modify the model to match the number of classes in the dataset
num_classes = df.shape[1] - 1

# Add dropout before the final fully connected layer
model.classifier[3] = nn.Sequential(
    nn.Dropout(p=0.2),  # 20% dropout
    nn.Linear(model.classifier[3].in_features, num_classes)
)

# Unfreeze the classifier layers
for param in model.classifier.parameters():
    param.requires_grad = True

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(device)

# Load the model state
model.load_state_dict(torch.load("/home/azureuser/preloved/store/ai_model.pth", map_location=torch.device('cpu')))
print(model.eval())  # Set model to evaluation mode

    
"""
storage_worker = StorageWorker()


def check_post(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return return_not_auth()

        if request.method != "POST":
            return return_not_post()

        # Call the original view function
        return view_func(request, *args, **kwargs)

    return wrapper



def return_not_post():
    return JsonResponse({'error': 'not a post-type request'}, status=400)


def thumbnailify(id):
    set = Slug.objects.filter(itemID=id, isThumbnail=1)
    if set is None:
        return 1
    return 0


# Create your views here.

def return_id_not_found():
    return JsonResponse({'error': 'Specified id not found.'}, status=400)


def return_not_auth():
    # raise Exception("User not authenticated")
    return JsonResponse({'error': 'user not authenticated'}, status=400)


class ShopController:

    @staticmethod
    def get_store_owner(request) -> ShopOwner | None:
        if not request.user.is_authenticated:
            return_not_auth()
        try:
            return ShopOwner.objects.filter(userID=request.user).first()
        except Exception as e:
            return None

    @staticmethod
    def get_store(request):
        try:
            owner = ShopController.get_store_owner(request)

            return Store.objects.filter(shopOwnerID=owner).first()
        except Exception as e:
            return None

    def new_store(self, request):
        if not request.user.is_authenticated:
            if not request.user.is_staff:
                return return_not_auth()
        ## IMPLEMENT!

    def get_all_items(self, request):
        if not request.user.is_authenticated:
            if not request.user.is_staff:
                return return_not_auth()
        try:
            id = int(request.GET.get('id'))
            sets = Item.objects.filter(storeID=Store.objects.filter(storeid=id).first())
            items = []
            for item in sets:
                items.append(item.itemID)
            return JsonResponse(items)
        except Exception as e:
            return return_id_not_found()

    def add_item(self, request):
        if not request.user.is_authenticated:
            if not request.user.is_staff:
                return return_not_auth()
        if request.method != 'POST':
            return return_not_post()
        POST = request.POST
        store = self.get_store(request)

        
        description = POST.get('description')
        style = int(POST.get('isFeminine'))
        name = POST.get('name')
        tagID = int(POST.get('tagID'))
        price = float(POST.get('price'))
        size = str(POST.get('size'))
        valid_sizes = ('XL', 'XS', 'S', 'M', 'L')
        if size not in valid_sizes:
            return JsonResponse(
                {'error': 'The size "' + size + '" is not valid. Please use valid sizes ' + str(valid_sizes) + "."},
                status=400)

        t = Tag.objects.filter(tagID=tagID).first()
        size = Size(sizeType=size)
        size.save()
        if store is None:
            return JsonResponse({'error': 'Shop has no store'}, status=400)
        item = Item(storeID=store, description=description, isFeminine=style, name=name, price=price, size=size)
        item.save()
        self.attach_size_to_item(item.itemID, size)
        ItemTag(tag=t, item=item).save()
        return JsonResponse({'response': 'Ok!', 'generatedID': item.itemID})

    def attach_size_to_item(self, item_id, size):
        s = Size.objects.filter(sizeType=size).first()
        i = Item.objects.filter(itemID=item_id).first()
        i.size = s

    def get_all_tags(self, request):
        tags = {}
        for x in Tag.objects.all():
            tags[x.name] = x.tagID
        return JsonResponse(tags)

    def create_new_shop(self, request):
        if not request.user.is_authenticated:
            if not request.user.is_staff:
                return return_not_auth()
        if request.method != 'POST':
            return return_not_post()
        address = request.POST.get('address')
        location = Location(address_plain=address)
        location.save()
        name = request.POST.get('name')
        owner = self.get_store_owner(request)
        if owner is None:
            return JsonResponse({'error': 'User is not a shop owner'}, status=400)
        store = Store(shopOwnerID=owner, locationID=location, storeName=name)
        store.save()
        return JsonResponse({'response': 'Ok!', 'storeID': store.storeID})

    @staticmethod
    def attach_image_to_item(request):
        if request.method != 'POST':
            return return_not_post()

        imgStream = request.FILES.get('img')
        imgStream.seek(0)  # Reset the file pointer to the beginning
        imgID = int(request.POST.get('id'))
        item = Item.objects.filter(itemID=imgID).first()
        if item is None:
            return return_id_not_found()
        slugString = storage_worker.upload_in_namespace(request, imgStream, namespace='item_images/',
                                                        slug=imgStream.name)
        if slugString is None:
            return return_not_auth()
        slug = Slug(slug=slugString, itemID=item, isThumbnail=thumbnailify(imgID))
        slug.save()

        imgStream.seek(0)  # Reset the file pointer to the beginning
        # Convert to Base64
        img_bytes = imgStream.read()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        client = weaviate.connect_to_custom(
            http_host="34.87.112.226",
            http_port=8080,
            http_secure=False,
            grpc_host="34.87.112.226",
            grpc_port=50051,
            grpc_secure=False,
        )
        errors = []
        try:
            items = client.collections.get("ItemMM")
            item_obj = {
                "itemId": item.itemID,
                "image": img_base64,
                "name": item.name,
                "description": item.description,
            }
            with items.batch.dynamic() as batch:
                batch.add_object(properties=item_obj, uuid=generate_uuid5(item.itemID))
            # Check for failed objects
            if len(items.batch.failed_objects) > 0:
                print(f"Failed to import {len(items.batch.failed_objects)} objects")
                for failed in items.batch.failed_objects:
                    print(f"e.g. Failed to import object with error: {failed.message}")
                    errors.append(failed.message)
        finally:
            client.close()

        return JsonResponse({'response': 'Ok!', 'slug': slugString, 'errors': errors, 'itemObj': item_obj})

    @staticmethod
    def auto_tag_item(request):
        if request.method != 'POST':
            return return_not_post()
        
        params = request.FILES.get('img')
        extractor = VGGFeatureExtractor()
        # Extract features from the uploaded image
        features = extractor.extract_features(params.read())
        items = query_database_by_image(features.tolist(),3)

        # Get tags for each item and count their frequency
        tag_frequency = {}
        for item in items:
            tags = ItemTag.objects.filter(item=item)
            for tag in tags:
                tag_name = tag.tag.name
                if tag_name in tag_frequency:
                    tag_frequency[tag_name] += 1
                else:
                    tag_frequency[tag_name] = 1
        
        # Get the top 3 tags
        top_tags = sorted(tag_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Store the tag names in a list
        top_tag_names = [tag[0] for tag in top_tags]

        # Return the top tag names as JSON response
        return JsonResponse({"data":top_tag_names})

        



        """
        image_file = request.FILES.get('img')
        image = Image.open(image_file).convert('RGB')
        image_tensor = preprocess(image).unsqueeze(0)  # Preprocess and add batch dimension
        image_tensor = image_tensor.to(device)

        with torch.no_grad():
            outputs = model(image_tensor)
            preds = torch.sigmoid(outputs) > 0.4  # Apply sigmoid and threshold

        predictions = preds.cpu().numpy()

        labels = df.columns[1:]  # Assuming first column is 'Image name'
        predicted_labels = {label: bool(pred) for label, pred in zip(labels, predictions[0])}

        # Filter only the true labels
        true_labels = [label for label, is_true in predicted_labels.items() if is_true]

        """
        return JsonResponse({"status": "service not available"}, status=404)

    @staticmethod
    def get_item_images(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        id = request.GET.get('id')
        item = Item.objects.filter(itemID=id).first()
        links = Slug.objects.filter(itemID=item, isDeleted=0)
        link_list = []
        for link in links:
            link_list.append("https://preloved.westus2.cloudapp.azure.com/media/" + link.slug)
        return JsonResponse({'id' : id, 'image_links' : link_list})

    
    @staticmethod
    def get_item_details(request):
        if not request.user.is_authenticated:
            return return_not_auth()

        response = {}
        id = int(request.GET.get('id'))
        retrieved = Item.objects.filter(itemID=id).first()
        if retrieved is None:
            return return_id_not_found()
        response['itemID'] = retrieved.itemID
        response['storeID'] = retrieved.storeID.storeID
        response['storeName'] = retrieved.storeID.storeName
        response['size'] = retrieved.size.sizeType
        response['name'] = retrieved.name
        response['description'] = retrieved.description
        response['isFeminine'] = bool(retrieved.isFeminine)
        response['price'] = retrieved.price
        tags = ItemTag.objects.filter(item=retrieved)
        item_tags = []
        for tag in tags:
            item_tags.append({'tagName': tag.tag.name, 'tagID': tag.tag.tagID})
        response['tags'] = item_tags

        return JsonResponse(response)

    @staticmethod
    def attach_tag_to_item(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        if not request.method == 'POST':
            return return_not_post()
        item = Item.objects.filter(itemID=int(request.POST.get('itemID'))).first()
        tag = Tag.objects.filter(tagID=int(request.POST.get('tagID'))).first()
        itemTag = ItemTag(item=item, tag=tag)
        itemTag.save()
        return JsonResponse({'response' : 'ok!'})

    @staticmethod
    def get_balance(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        ownerID = int(request.GET.get('id'))
        s = ShopOwner.objects.filter(id=ownerID).first()

        if s is None:
            return return_id_not_found()
            
        return JsonResponse({'balance': s.balance})

    @staticmethod
    def add_balance(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        if not request.user.is_superuser:
            return return_not_auth()
        id = int(request.POST['id'])
        owner = ShopOwner.objects.filter(id=id).first()
        if owner is None:
            return return_id_not_found()
        owner.balance = float(request.POST['increase'])
        owner.save()
        return JsonResponse({'response': 'OK!', 'balance': owner.balance})


    @staticmethod
    def modify_balance(request):
        shopOwner = ShopController.get_store_owner(request)
        increase = request.POST.get('incr')
        ShopController.change_balance(shopOwner, increase)

    # Changes the balance without needing a request
    @staticmethod
    def change_balance(shopOwner: ShopOwner, modifyByAmount: float):
        balance = float(shopOwner.balance)
        balance += modifyByAmount
        shopOwner.balance = balance
        shopOwner.save()


    @staticmethod
    def generate_random_vouchers(num_vouchers):
        voucher_values = [100, 200, 300, 500, 1000, 5000, 10000]

        for _ in range(num_vouchers):
            voucher_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz', k=20))
            value = random.choice(voucher_values)

            # Create a new LoadVoucher instance
            voucher = LoadVoucher(voucher_code=voucher_code, value=value)
            voucher.save()

    # Example usage: generate 10 random vouchers

    @staticmethod
    @check_post
    def redeem_voucher(request):
        code = request.POST.get('code')
        voucher = LoadVoucher.objects.filter(voucher_code=code).first()
        if voucher is None:
            return JsonResponse({'error': f"the voucher '{code}' is not valid"}, status=400)
        shopOwner = ShopController.get_store_owner(request)
        if shopOwner is None:
            return JsonResponse({'error': 'the current user is not a shop owner'}, status=400)
        if voucher.is_redeemed == 1:
            return JsonResponse({'error' : 'the voucher has already been redeemed'}, status=400)
        shopOwner.balance += voucher.value
        voucher.is_redeemed = 1
        voucher.save()
        shopOwner.save()
        return JsonResponse({'response' : 'ok!', 'new balance': shopOwner.balance})


    @staticmethod
    def codegen(request):
        if request.user.is_superuser:
            set = LoadVoucher.objects.filter(is_redeemed=0).order_by('?')[:10]
            returning_value = []
            for voucher in set:
                returning_value.append({'voucher code' : voucher.voucher_code, 'amount': voucher.value})
            return JsonResponse({'message': 'These are valid, non-redeemed vouchers. Only ten valid vouchers are displayed at a time.','valid vouchers: ': returning_value})
        return JsonResponse({'error' : 'limited credentials'}, status=400)

    
    
    @staticmethod
    def get_stores(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        shopOwner = ShopOwner.objects.filter(userID=request.user).first()
        if shopOwner is None:
            return JsonResponse({'error' : 'user is not a shop owner / does not have a store'})
        stores_set = Store.objects.filter(shopOwnerID=shopOwner)
        stores = []
        resulting = {
            "userID" : request.user.id,
            "shopOwnerID" : shopOwner.id,
            "email": request.user.username,
            "phoneNumber" : shopOwner.phoneNumber,
            "balance" : shopOwner.balance,
            "isVerified": shopOwner.isVerified,
            "stores": stores
        }

        for store in stores_set:
            store_entity = {}
            store_entity['storeID'] = store.storeID
            store_entity['storeName'] = store.storeName
            store_entity[''] = store.locationID.address_plain
            stores.append(store_entity)

        return JsonResponse(resulting)

    @staticmethod
    def get_shop_details(request):
        query = request.GET.get('shopID')
        if query is None:
            return JsonResponse({'error' : 'shopID is required'})
        if not request.user.is_authenticated:
            return return_not_auth()
        shop: Store = Store.objects.filter(storeID=query).first()
        if shop is None:
            return return_id_not_found()
        return JsonResponse({
            'shopID': query,
            'shopName': shop.storeName,
            'location' : shop.locationID.address_plain
        })

    @staticmethod
    def get_shop_items(request):
        if not request.user.is_authenticated:
            return_not_auth()
        owner = ShopController.get_store_owner(request)
        if owner is None:
            return return_not_auth()
        shop: Store = Store.objects.filter(shopOwnerID=owner).first()
        if shop is None:
            return JsonResponse({'error' : 'owner does not have a shop'})
        item_set = Item.objects.filter(storeID=shop)
        items = []
        for item in item_set:
            item_entity = {
                'itemID': item.itemID,
                'itemName': item.name
            }
            items.append(item_entity)
        return JsonResponse({'items:': items})










shopController = ShopController()




def add_item(request):
    return shopController.add_item(request)


def get_all_tags(request):
    return shopController.get_all_tags(request)


def create_new_shop(request):
    return shopController.create_new_shop(request)

def auto_tag_item(request):
    return shopController.auto_tag_item(request)
