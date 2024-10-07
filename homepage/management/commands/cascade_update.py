from django.core.management.base import BaseCommand
from models.services import cascade_update_on_startup

class Command(BaseCommand):
    help = 'Runs the cascade update on startup function'

    def handle(self, *args, **options):
        self.stdout.write('Starting cascade update...')
        cascade_update_on_startup()
        self.stdout.write(self.style.SUCCESS('Cascade update completed successfully'))