import time
from django.shortcuts import render
from django.http import JsonResponse
from .models import ChatMessage
from store.models import Store
from preloved_auth.models import ShopUser, ShopOwner

# Create your views here.
def long_poll_messages(request):
    timeout = 30
    start_time = time.time()
    user_id = request.GET.get('userID')
    seller_id = request.GET.get('sellerID')
    
    while time.time() - start_time < timeout:
        # Get unread messages
        messages = ChatMessage.objects.filter(userID=user_id, sellerID=seller_id, is_read=False).order_by('timestamp')
        if messages.exists():
            # Mark the messages as read
            messages.update(is_read=True)
            return JsonResponse({'messages': list(messages.values())})
        time.sleep(1)

    return JsonResponse({'error': 'no new messages'}, status=400)

def send_message(request):
    user_id = request.POST.get('userID')
    seller_id = request.POST.get('sellerID')
    message = request.POST.get('message')

    if not user_id or not seller_id or not message:
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    new_message = ChatMessage(
        message=message,
        userID=user_id,
        sellerID=seller_id,
    )
    new_message.save()

    return JsonResponse({'success': 'Message sent successfully'})

def fetch_all_messages(request):
    user_id = request.GET.get('userID')
    seller_id = request.GET.get('sellerID')

    messages = ChatMessage.objects.filter(userID=user_id, sellerID=seller_id).order_by('timestamp')
    messages.update(is_read=True)

    messages_list = list(messages.values('id', 'userID', 'sellerID', 'message', 'timestamp', 'is_read', 'sender'))

    return JsonResponse({'messages': messages_list})

def fetch_chat_history_user(request):
    user = ShopUser.objects.get(userID=request.user)

    chat_info_set = set()  # Use a set to prevent duplicates
    messages = ChatMessage.objects.filter(userID=user.userID.id).order_by('timestamp')

    for message in messages:
        print(message)
        shopOwner = ShopOwner.objects.filter(userID=message.sellerID).first()
        store = Store.objects.filter(shopOwnerID=shopOwner).first()
        if store:
            # Add a tuple of (sellerID, storeName) to the set to ensure uniqueness
            chat_info_set.add((message.sellerID, store.storeName))

    # Convert the set to a list of dictionaries with 'id' and 'name' keys
    chat_info = [{'id': seller_id, 'name': store_name} for seller_id, store_name in chat_info_set]

    return JsonResponse({'chat_info': chat_info})

def fetch_chat_history_seller(request):
    seller = ShopOwner.objects.get(userID=request.user)

    chat_info_set = set()  # Use a set to prevent duplicates
    messages = ChatMessage.objects.filter(sellerID=seller.userID).order_by('timestamp') 
    
    for message in messages:
        customer = ShopUser.objects.filter(userID=message.userID).first()
        if customer:
            # Add a tuple of (userID, customerName) to the set to ensure uniqueness
            customer_name = f"{customer.first_name} {customer.last_name}"
            chat_info_set.add((message.userID, customer_name))

    # Convert the set to a list of dictionaries with 'id' and 'name' keys
    chat_info = [{'id': user_id, 'name': customer_name} for user_id, customer_name in chat_info_set]

    return JsonResponse({'chat_info': chat_info})

def get_seller_id(request):
    storeID = request.GET.get('storeID')
    store = Store.objects.get(storeID=storeID)
    shop_owner_id = store.shopOwnerID.userID.id
    store_name = store.storeName

    return JsonResponse({'shopOwnerID': shop_owner_id, 'storeName': store_name})
