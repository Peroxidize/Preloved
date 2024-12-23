# Create your views here.
import secrets
import string
import os

import django.db
from django.views.decorators.csrf import get_token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse

from preloved import preloved_secrets
from .models import ShopUser, ShopOwner, Location, ShopVerification, Staff, Store
from django.core.files.storage import default_storage as storage
from django.core.files.base import ContentFile
from datetime import datetime
from storage.views import StorageWorker
import json

storage_worker = StorageWorker()


def get_file_extension(file_object):
    # Get the file name from the file object
    file_name = os.path.basename(file_object.name)

    # Split the file name into the base name and extension
    _, extension = os.path.splitext(file_name)

    return extension


class LoginController:

    def loginAPI(self, request):
        result = assert_post(request)
        if result:
            return result
        u = authenticate(username=request.POST['email'], password=request.POST['password'])
        if u is not None:
            login(request, u)
            value = {}
            value['id'] = request.user.id
            value['first name'] = request.user.first_name
            value['last name'] = request.user.last_name
            value['email'] = request.user.email
            s = ShopOwner.objects.filter(userID=request.user).first()
            if request.user.is_superuser:
                value['user_type'] = 'Admin'
                value['user_type_int'] = 3
            elif s is None:
                value['user_type'] = 'Shop User'
                value['user_type_int'] = 0
            else:
                staff = Staff.objects.filter(uID=request.user).first()
                if staff is not None:
                    value['user_type'] = 'Verification Officer'
                    value['user_type_int'] = 2
                else:
                    shop_ver_instance = ShopVerification.objects.filter(shopOwnerID=s.id).first()
                    value['user_type'] = 'Shop Owner'
                    value['user_type_int'] = 1
                    value['verified'] = shop_ver_instance.status
                    value['shop_owner_id'] = s.id

            value['sessionID'] =  request.COOKIES.get('sessionid')
            return JsonResponse(value)
        return JsonResponse({'error': 'Invalid credentials'}, status=400)

    def logoutAPI(self, request):
        if request.user.is_authenticated:
            logout(request)
            return JsonResponse({'status': 'OK!'})
        return JsonResponse({'error': 'user not authenticated'}, status=400)

    def is_logged_in(self, request):
        if request.user.is_authenticated:
            return JsonResponse({'response': True, 'sessionid' : request.COOKIES.get('sessionid')}, )
        return JsonResponse({'response': False, 'sessionid' : request.COOKIES.get('sessionid')})


controller = LoginController()

def return_not_post():
    return JsonResponse({'error': 'not a post-type request'}, status=400)

def return_not_auth():
    return JsonResponse({'error': 'user not authenticated'}, status=400)


def generate_id(request):
    length = 12
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return JsonResponse({'response' : random_string})


def assert_post(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'not a post-type request'}, status=400)


class SignUpController:

    def new_shop_user(self, request):
        result = assert_post(request)
        if result:
            return result
        try:
            email = request.POST['email']
            password = request.POST['password']
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            phone_no = request.POST['phone_no']
            isFeminine = int(request.POST['isFeminine'])
            locationID = None
            
            # Handle both list and JSON string formats
            tag_ids = request.POST.getlist('tagIDs')
            if not tag_ids:
                tag_ids = json.loads(request.POST.get('tagIDs', '[]'))
            
            u = User.objects.create_user(username=email, email=email, password=password, first_name=first_name, last_name=last_name, is_staff=1)
            shop_user = ShopUser.objects.create(userID=u, phone_no=phone_no, locationID=locationID, is_feminine=isFeminine)

            # Create Preferences object for the user
            preferences, created = Preferences.objects.get_or_create(user=u)

            # Attach preferences if tagIDs are provided
            tags_to_add = []
            for tag_id in tag_ids:
                tag = Tag.objects.filter(tagID=int(tag_id)).first()
                if tag:
                    tags_to_add.append(tag)
            
            # Use set() method to add tags to the many-to-many relationship
            preferences.tags.set(tags_to_add)

        except KeyError as key_error:
            return JsonResponse({'error': f'Missing required parameter: {key_error}'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid tagIDs format. Expected JSON array or multiple form entries.'}, status=400)

        except Exception as ex:
            msg = f'Error: {str(ex)}'
            print('Error:', msg)
            return JsonResponse({'error': msg}, status=400)

        storage.save(f'users/{email}/init.txt', ContentFile(f"autogenerated::{str(datetime.now())}".encode('utf-8')))
        return JsonResponse({'status': 'OK!'})

    def new_shop_owner(self, request):
        result = assert_post(request)
        if result:
            return result
        email = request.POST['email']
        password = request.POST['password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        phone_no = request.POST['phone_no']
        address_line = request.POST['address']
        u = User.objects.create_user(email=email, username=email, password=password,
                                     first_name=first_name, last_name=last_name)
        l = Location.objects.create(address_plain=address_line)
        s = ShopOwner.objects.create(userID=u, phoneNumber=phone_no, locationID=l)
        ShopVerification(shopOwnerID=s).save()
        return JsonResponse({'response': 'Ok!'})

    def shop_id_one(self, request):
        result = assert_post(request)
        if result:
            return result
        if request.user.is_authenticated:
            shop_owner = ShopOwner.objects.filter(userID=request.user).first()
            slugs = ShopVerification.objects.filter(shopOwnerID=shop_owner).first()
            file = request.FILES['file']
            file_path = storage_worker.upload_in_namespace(request, file, namespace='verification/', slug=file.name)

            if file_path is None:
                return return_not_auth()
            slugs.idSlug1 = file_path
            slugs.save()
            return JsonResponse({'response': 'Ok!'})
        return return_not_auth()

    def shop_id_two(self, request):
        result = assert_post(request)
        if result:
            return result
        if request.user.is_authenticated:
            shop_owner = ShopOwner.objects.filter(userID=request.user).first()
            slugs = ShopVerification.objects.filter(shopOwnerID=shop_owner).first()
            file = request.FILES['file']
            file_path = storage_worker.upload_in_namespace(request, file, namespace='verification/', slug=file.name)
            slugs.idSlug2 = file_path
            slugs.save()
            return JsonResponse({'response': 'Ok!'})
        return return_not_auth()

    def shop_id_selfie(self, request):
        result = assert_post(request)
        if result:
            return result
        if request.user.is_authenticated:
            shop_owner = ShopOwner.objects.filter(userID=request.user).first()
            slugs = ShopVerification.objects.filter(shopOwnerID=shop_owner).first()
            file = request.FILES['file']
            file_path = storage_worker.upload_in_namespace(request, file, namespace='verification/', slug=file.name)
            slugs.selfieSlug = file_path
            slugs.save()
            return JsonResponse({'response': 'Ok!'})
        return return_not_auth()
    
    def attach_pref_to_user(request):
        if request.method != 'POST':
            return return_not_post()
        
        try:
            # Handle both list and JSON string formats
            tag_ids = request.POST.getlist('tagIDs')
            if not tag_ids:
                tag_ids = json.loads(request.POST.get('tagIDs', '[]'))
            
            # Convert tag_ids to integers
            tag_ids = [int(tag_id) for tag_id in tag_ids]
            
            # Get or create a single Preferences object for the user
            pref, created = Preferences.objects.get_or_create(user=request.user)
            
            # Get all valid tags from the provided tag_ids
            new_tags = Tag.objects.filter(tagID__in=tag_ids)
            
            # Use set() to completely replace existing tags with the new set
            # This will automatically remove tags that aren't in the new set
            pref.tags.set(new_tags)
            
            # Get updated preferences for response
            updated_tags = pref.tags.all()
            response_data = {
                'response': 'ok!',
                'updated_preferences': {
                    tag.name: tag.tagID for tag in updated_tags
                }
            }
            
            return JsonResponse(response_data)
        
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid tagIDs format. Expected JSON array or multiple form entries.'
            }, status=400)
        
        except ValueError:
            return JsonResponse({
                'error': 'Invalid tag ID format. All tag IDs must be integers.'
            }, status=400)
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
        
    def get_pref_for_user(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        
        try:
            preferences, created = Preferences.objects.get_or_create(user=request.user)
            tags = preferences.tags.all()
            tag_dict = {tag.name: tag.tagID for tag in tags}
            return JsonResponse(tag_dict)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    


class VerificationController:

    def document_status(self, request):
        if not request.user.is_authenticated:
            if Staff.objects.filter(uID=request.user.id) is None:
                return return_not_auth()

            # Retrieve the 'id' from the GET request parameters
        id = request.GET.get('id')

        response = {}
        owner = ShopVerification.objects.filter(shopOwnerID=id).first()

        if not owner:
            response['status'] = 'not found'
        elif owner.idSlug1 == '':
            response['status'] = 'id 1 is missing'
        elif owner.idSlug2 == '':
            response['status'] = 'id 2 is missing'
        elif owner.selfieSlug == '':
            response['status'] = 'selfie is missing'
        else:
            response['status'] = 'complete'

        return JsonResponse(response)

    def get_image(self, request):
        if not request.user.is_authenticated:
            if Staff.objects.filter(uID=request.user.id) is None:
                return return_not_auth()

        # Get parameters from GET request
        id = request.GET.get('id')
        resource_type = request.GET.get('resource_type')

        if id is None or resource_type is None:
            raise Exception(
                f"Cannot find missing resource type and id where id is {id} and resource type {resource_type}")

        # Retrieve the owner object based on the id
        owner = ShopVerification.objects.filter(shopOwnerID=id).first()

        if not owner:
            raise Exception("Owner of image not found")

        # Determine the image slug based on the resource_type
        if resource_type == "id1":
            image_slug = owner.idSlug1
        elif resource_type == "id2":
            image_slug = owner.idSlug2
        elif resource_type == "selfie":
            image_slug = owner.selfieSlug
        else:
            raise Exception("Cannot find resource type")

        # Assuming img is a binary image file
        img = storage_worker.get_absolute(request, image_slug)

        if img:
            response = HttpResponse(img, content_type='image/png')  # Adjust content type based on the image format
            response['Content-Disposition'] = f'inline; filename={image_slug}.png'  # Set a filename for the image
            return response
        else:
            # Handle the case when the image is not found
            raise Exception("Cannot find image")

    def get_shop_owner_details(self, request):
        if not request.user.is_authenticated:
            if Staff.objects.filter(uID=request.user.id) is None:
                return return_not_auth()
        id = request.GET.get('id')
        user = None
        shop_owner = None
        try:
            shop_owner = ShopOwner.objects.filter(id=id).first()
            user = User.objects.filter(id=shop_owner.userID_id).first()
        except Exception as e:
            return JsonResponse({'error': 'Cannot find queried user.'}, status=400)
        shop_details = {}
        shop_details['isVerified'] = shop_owner.isVerified
        shop_details['email'] = user.email
        shop_details['first_name'] = user.first_name
        shop_details['last_name'] = user.last_name
        return JsonResponse(shop_details)

    def get_list_pending(self, request):
        if not request.user.is_authenticated:
            if Staff.objects.filter(uID=request.user.id) is None:
                return return_not_auth()
        to_verify = []
        for user in ShopVerification.objects.filter(status=0):
            to_verify.append(user.id)
        final = []
        for pending in to_verify:
            user = None
            shop_owner = None
            try:
                shop_owner = ShopOwner.objects.filter(id=pending).first()
                user = User.objects.filter(id=shop_owner.userID_id).first()
            except Exception as e:
                return JsonResponse({'error': 'Cannot find queried user.'}, status=400)
            shop_details = {}
            shop_details['id'] = pending
            shop_details['isVerified'] = shop_owner.isVerified
            shop_details['email'] = user.email
            shop_details['first_name'] = user.first_name
            shop_details['last_name'] = user.last_name
            final.append(shop_details)

        return JsonResponse({'response' : final})

    def approve_or_reject(self, request):
        if request.method != 'POST':
            return return_not_post()
        if not request.user.is_authenticated:
            if Staff.objects.filter(uID=request.user.id) is None:
                return return_not_auth()
        id = request.POST['id']
        status = int(request.POST['updated_status'])
        try:
            obj = ShopVerification.objects.filter(shopOwnerID=id).first()
            obj.status = status
            obj.save()
            return JsonResponse({'response': 'Ok!'})
        except Exception as e:
            return JsonResponse({'error': 'Invalid Shop Owner ID.'}, status=400)


    def get_current_user(self, request):
        try:
            if not request.user.is_authenticated:
                return return_not_auth()

            value = {}
            value['id'] = request.user.id
            value['first name'] = request.user.first_name
            value['last name'] = request.user.last_name
            value['email'] = request.user.email
            s = ShopOwner.objects.filter(userID=request.user).first()
            if request.user.is_superuser:
                value['user_type'] = 'Admin'
                value['user_type_int'] = 3
            elif s is None:
                value['user_type'] = 'Shop User'
                value['user_type_int'] = 0
                value['shop_user_id'] = ShopUser.objects.get(userID=request.user).id
            else:
                staff = Staff.objects.filter(uID=request.user).first()
                if staff is not None:
                    value['user_type'] = 'Verification Officer'
                    value['user_type_int'] = 2
                else:
                    value['user_type'] = 'Shop Owner'
                    value['user_type_int'] = 1
                    value['verified'] = s.isVerified
                    value['shop_owner_id'] = s.id



            return JsonResponse(value)

        except Exception as e:
            return JsonResponse({'error': str(e)})


verificationController = VerificationController()
signUpController = SignUpController()


## DOCUMENTATION STARTS HERE
## Following format:
## Endpoint Name
## Endpoint URL
## Endpoint METHOD (post, get)


def shop_id_one(request):
    return signUpController.shop_id_one(request)


def shop_id_two(request):
    return signUpController.shop_id_two(request)


def shop_id_selfie(request):
    return signUpController.shop_id_selfie(request)


def new_shop_user(request):
    return signUpController.new_shop_user(request)


def new_shop_owner(request):
    return signUpController.new_shop_owner(request)


def csrf_token(request):
    # Get the CSRF token using Django's get_token function
    csrf_token_value = get_token(request)

    # Return the CSRF token in a JSON response
    return JsonResponse({'csrf_token': csrf_token_value})


def loginAPI(request):
    return controller.loginAPI(request)


def logout_attempt(request):
    return controller.logoutAPI(request)


def is_logged_in(request):
    return controller.is_logged_in(request)


def get_image(request):
    return verificationController.get_image(request)


def document_status(request):
    return verificationController.document_status(request)


def get_shop_owner_details(request):
    return verificationController.get_shop_owner_details(request)


def get_list_pending(request):
    return verificationController.get_list_pending(request)


def approve_or_reject(request):
    return verificationController.approve_or_reject(request)



def get_current_user(request):
    return verificationController.get_current_user(request)


def get_link(request):
    if not request.user.is_superuser:
        return JsonResponse({'error' : 'insufficient credentials'})
    id = request.GET.get('id')
    shop = ShopOwner.objects.filter(id=int(id)).first()
    if shop is None:
        return JsonResponse({'error': 'user is not shop owner'})
    verification = ShopVerification.objects.filter(shopOwnerID=shop).first()
    links = []
    resulant = {'result': links}
    links.append(preloved_secrets.STORAGE+verification.idSlug1)
    links.append(preloved_secrets.STORAGE + verification.idSlug2)
    links.append(preloved_secrets.STORAGE + verification.selfieSlug)
    return JsonResponse(resulant)


from store.models import Preferences, Store, Tag
class LocationController:

    @staticmethod
    def attach_location(request):
        if not request.user.is_authenticated:
            return return_not_auth()
        location = Location(longitude=request.POST.get('long'), latitude=request.POST.get('lat'))
        location.save()
        owner:ShopOwner = ShopOwner.objects.filter(userID=request.user).first()
        if owner is not None:
            owner.locationID = location
            owner.save()
            with django.db.connection.cursor() as cursor:
                query = f"""
                SELECT storeID from store_store where {owner.id} = shopOwnerID_id
                """
                cursor.execute(query)
                _id = cursor.fetchone()[0]
                store = Store.objects.filter(storeID=_id).first()
            store.locationID = location
            store.save()
            return JsonResponse({'success': True})

        user = ShopUser.objects.get(userID=request.user)
        user.locationID = location
        return JsonResponse({'success': True})

    @staticmethod
    def get_location_link(request):
        from store.models import Store
        shopUser = ShopUser.objects.get(userID=request.user.id)
        shopID = request.GET.get('shopID')
        if shopID is None:
            return JsonResponse({'error' : 'invalid shop id'})
        store = Store.objects.get(storeID=shopID)
        if store.locationID.latitude is None or store.locationID.longitude is None:
            return JsonResponse({'error' : 'Shop does not have inferred location yet'})

        return JsonResponse({'path':
                             LocationController.generate_maps_link(request.GET.get('lat'),
                                                                   request.GET.get('long'),
                                                                   store.locationID.latitude,
                                                                   store.locationID.longitude)})


    @staticmethod
    def generate_maps_link(origin_lat, origin_lng, destination_lat, destination_lng):
        base_url = "https://www.google.com/maps/dir/?api=1"
        origin = f"origin={origin_lat},{origin_lng}"
        destination = f"destination={destination_lat},{destination_lng}"
        maps_link = f"{base_url}&{origin}&{destination}"
        return maps_link








