from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create superuser if none exists'

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Superuser already exists, skipping.')
            return

        username = 'admin'
        password = 'admin123'
        User.objects.create_superuser(username, 'admin@simplehotel.com', password)
        self.stdout.write(self.style.SUCCESS(f'Superuser created: {username} / {password}'))
