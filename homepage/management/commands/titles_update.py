from django.core.management.base import BaseCommand
from models.services import cascade_update_on_startup
from store.models import Item
from models import title_model, vector_client

class Command(BaseCommand):
    help = 'Runs the cascade update on product titles on startup function'

    def handle(self, *args, **options):
        vector_client.delete_collection('title')
        title_model = vector_client.get_or_create_collection('title')
        items = Item.objects.all()
        for item in items:
            title_model.add(
                documents=[item.name],
                ids=[str(item.itemID)],
                metadatas=[{"item_id": item.itemID}]
            )
        self.stdout.write(self.style.SUCCESS('Titles update completed successfully'))
