from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from pathlib import Path

from hotel_alpha.models import Hotel


class Command(BaseCommand):
    help = 'Upload locally-stored hotel images to the configured media storage (Cloudinary)'

    def handle(self, *args, **options):
        storage_name = getattr(settings, 'DEFAULT_FILE_STORAGE', 'local (FileSystemStorage)')
        self.stdout.write(f"Active media storage: {storage_name}")

        if 'cloudinary' not in str(storage_name).lower():
            self.stdout.write(
                self.style.WARNING(
                    "Cloudinary is NOT active. Set CLOUDINARY_URL in .env (or Render env vars) "
                    "before running this command."
                )
            )
            return

        uploaded = 0
        skipped = 0
        for hotel in Hotel.objects.exclude(image=''):
            name = hotel.image.name
            local_path = Path(settings.MEDIA_ROOT) / name
            if not local_path.exists():
                self.stdout.write(self.style.WARNING(f"  skipped (not on disk): {name}"))
                skipped += 1
                continue

            with local_path.open('rb') as f:
                hotel.image.save(name, File(f), save=True)

            self.stdout.write(self.style.SUCCESS(f"  uploaded: {name} -> {hotel.image.url}"))
            uploaded += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Uploaded {uploaded}, skipped {skipped}."))
