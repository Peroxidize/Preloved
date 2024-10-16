from store.models import Item, Slug
from .migrations.image_transformer import VGGFeatureExtractor, download_image

from .migrations.image_transformer import download_image
from . import central_model, vector_client, title_model


def cascade_update_on_startup():
    vector_client.delete_collection(name="central")
    # Create a new collection for the central model
    new_central_model = vector_client.get_or_create_collection('central')

    # Update the central_model reference
    global central_model
    central_model = new_central_model
    print("Central model has been reset and a new collection has been created.")
    objects = Slug.objects.all()
    extractor = VGGFeatureExtractor()
    cnt = 1
    for obj in objects:
        print(f"Loading: {cnt}/{len(objects)}, with actual slug {obj.slug}")
        cnt += 1
        img = download_image(obj.slug)
        add_vector_to_database(obj.slugID, extractor.extract_features(img), obj.itemID.itemID)
        obj.isModelRegistered = True
        obj.save()
    print("Cascade update completed successfully")


def add_vector_to_database(slug_id, vector, item_id):
    central_model.add(
        ids=[str(slug_id)],
        embeddings=[vector],
        metadatas={
            "item_id": item_id
        }
    )
    return

def add_title_to_database(item):
    """
    Add a product title to the title_model collection.
    
    :param item: An Item object containing the product information.
    """
    title_model.add(
        documents=[item.name],
        ids=[str(item.itemID)],
        metadatas=[{"item_id": item.itemID}]
    )
    print(f"Added title '{item.name}' with ID {item.itemID} to title_model.")

def query_database_by_title(title, n=20, not_equal_to=None):
    # Step 1: Query the database for similar vectors
    items = title_model.query(
        query_texts=[title],
        n_results=n
    )

    # Step 2: Extract the item_ids and apply the not_equal_to filter manually
    item_ids = []

    for idx, metadata in enumerate(items['metadatas'][0]):
        # If a filter is provided, exclude the item that matches 'not_equal_to'
        if metadata.get('item_id') != not_equal_to:
            item_ids.append(metadata.get('item_id'))




def query_database(vector_embeddings, n=20, not_equal_to=None):
    n+=1
    # Step 1: Query the database for similar vectors
    items = central_model.query(
        query_embeddings=[vector_embeddings],
        n_results=n
    )

    # Step 2: Extract the item_ids and apply the not_equal_to filter manually
    item_ids = []

    for idx, metadata in enumerate(items['metadatas'][0]):
        # If a filter is provided, exclude the item that matches 'not_equal_to'
        if metadata.get('item_id') != not_equal_to:
            item_ids.append(metadata.get('item_id'))

    return item_ids

def query_database_by_image(embeddings, n):
    # Query the central_model collection
    results = central_model.query(
        query_embeddings=[embeddings],
        n_results=n
    )

    # Extract item IDs from the results
    item_ids = [metadata['item_id'] for metadata in results['metadatas'][0]]

    # Prepare the query result
    query_result = []
    for itemID in item_ids:
        item = Item.objects.get(itemID=itemID)
        query_result.append(item)

    # Return the results as JSON
    return query_result
