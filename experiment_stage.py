import os
import django
from django.conf import settings

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "preloved.settings")

# Configure Django settings
django.setup()

# Import your function and necessary modules
from store.models import Slug
from models.services import cascade_update_on_startup, add_vector_to_database
from models.migrations.image_transformer import VGGFeatureExtractor, download_image

def test_cascade_update():
    print("Starting cascade update test...")
    cascade_update_on_startup()
    print("Cascade update test completed.")

if __name__ == "__main__":
    test_cascade_update()