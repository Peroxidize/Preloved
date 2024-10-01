from store.models import Slug
from .migrations.image_transformer import VGGFeatureExtractor, download_image

from .migrations.image_transformer import download_image
from . import central_model


def cascade_update_on_startup():
    objects = Slug.objects.filter(isModelRegistered=False)
    extractor = VGGFeatureExtractor()
    for obj in objects:
        img = download_image(obj.slug)
        add_vector_to_database(obj.slugID, extractor.extract_features(img))


def add_vector_to_database(slug_id, vector, item_id):
    central_model.add(
        ids=[str(slug_id)],
        embeddings=[vector],
        metadatas={
            "item_id": item_id
        }
    )
    return


def query_database(vector_embeddings, n=20, not_equal_to=None):
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