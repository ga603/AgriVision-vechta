from django.core.management.base import BaseCommand
from monitor.models import AgriculturalField

class Command(BaseCommand):
    help = 'Seeds the SQLite database with initial agricultural fields for testing'

    def handle(self, *args, **kwargs):
        # Check if fields already exist to avoid duplicates
        if AgriculturalField.objects.exists():
            self.stdout.write(self.style.WARNING('Database already contains field data. Skipping.'))
            return

        # Create a sample test field near the campus
        field = AgriculturalField.objects.create(
            name="Vechta Campus Test Plot",
            crop_type="Wheat",
            boundary_coordinates={
                "type": "Polygon",
                "coordinates": [[
                    [8.2700, 52.7200],
                    [8.2900, 52.7200],
                    [8.2900, 52.7400],
                    [8.2700, 52.7400],
                    [8.2700, 52.7200]
                ]]
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created field: {field.name}'))