from django.core.management.base import BaseCommand
from sortapp.models import SortedClothingCategory
from django.db import transaction

class Command(BaseCommand):
    help = 'Initialize predefined sorted clothing categories'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # Check if categories already exist
        if SortedClothingCategory.objects.exists():
            self.stdout.write(self.style.WARNING('Sorted clothing categories already exist. Skipping initialization.'))
            return

        # Define categories with their colors and icons
        categories = [
            {
                'name': 'Odzież damska',
                'description': 'Posortowana odzież damska',
                'icon': 'fa-female',
                'color': '#e83e8c',
            },
            {
                'name': 'Odzież męska',
                'description': 'Posortowana odzież męska',
                'icon': 'fa-male',
                'color': '#007bff',
            },
            {
                'name': 'Odzież dziecięca',
                'description': 'Posortowana odzież dziecięca',
                'icon': 'fa-child',
                'color': '#28a745',
            },
            {
                'name': 'Tekstylia domowe',
                'description': 'Posortowane tekstylia domowe',
                'icon': 'fa-bed',
                'color': '#ffc107',
            },
            {
                'name': 'Buty',
                'description': 'Posortowane buty',
                'icon': 'fa-shoe-prints',
                'color': '#dc3545',
            },
            {
                'name': 'Akcesoria',
                'description': 'Posortowane akcesoria',
                'icon': 'fa-briefcase',
                'color': '#6f42c1',
            },
            {
                'name': 'Odzież sportowa',
                'description': 'Posortowana odzież sportowa',
                'icon': 'fa-running',
                'color': '#20c997',
            },
            {
                'name': 'Premium',
                'description': 'Odzież markowa i wysokiej jakości',
                'icon': 'fa-crown',
                'color': '#fd7e14',
            },
            {
                'name': 'Odpady',
                'description': 'Odzież nienadająca się do ponownego użycia',
                'icon': 'fa-trash',
                'color': '#6c757d',
            },
        ]

        # Create categories
        for category_data in categories:
            SortedClothingCategory.objects.create(**category_data)
            self.stdout.write(self.style.SUCCESS(f'Created category: {category_data["name"]}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized sorted clothing categories'))