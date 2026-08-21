from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Check whether a superuser exists (does NOT create credentials)'

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Superuser exists, skipping.')
        else:
            self.stdout.write(
                self.style.WARNING(
                    'No superuser found. Create one manually: '
                    'python manage.py createsuperuser'
                )
            )
