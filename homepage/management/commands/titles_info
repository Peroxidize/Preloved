from django.core.management.base import BaseCommand
from models import title_model

class Command(BaseCommand):
    help = 'Get information about the Chroma database'

    def handle(self, *args, **options):
        # Get the count of items
        item_count = title_model.count()
        self.stdout.write(self.style.SUCCESS(f'There are currently {item_count} items in the Chroma database.'))

        # Get more detailed information
        collection_info = title_model.get()
        self.stdout.write(self.style.SUCCESS(f'Collection info: {collection_info}'))