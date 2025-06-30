from django.core.management.base import BaseCommand
from sortapp.models import IncomingClothing, Employee

class Command(BaseCommand):
    help = 'Creates initial data for the sorting application'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Creating initial data...'))
        
        # Create or update initial clothing categories
        self.create_clothing_categories()
        
        # Create initial employees if none exist
        self.create_initial_employees()
        
        self.stdout.write(self.style.SUCCESS('Initial data created successfully!'))
    
    def create_clothing_categories(self):
        # Create or update clothing categories with icons
        categories = [
            {
                'name': 'Odzież damska',
                'description': 'Ubrania damskie, sukienki, spódnice, bluzki',
                'icon': 'fa-person-dress',
                'color': '#e84393',
            },
            {
                'name': 'Odzież męska',
                'description': 'Ubrania męskie, koszule, spodnie, marynarki',
                'icon': 'fa-person',
                'color': '#0984e3',
            },
            {
                'name': 'Odzież dziecięca',
                'description': 'Ubrania dla dzieci w różnym wieku',
                'icon': 'fa-child',
                'color': '#3CB371',
            },
            {
                'name': 'Tekstylia domowe',
                'description': 'Pościel, ręczniki, obrusy, zasłony',
                'icon': 'fa-bed',
                'color': '#fdcb6e',
            },
            {
                'name': 'Buty',
                'description': 'Obuwie damskie, męskie i dziecięce',
                'icon': 'fa-shoe-prints',
                'color': '#d63031',
            },
            {
                'name': 'Akcesoria',
                'description': 'Torebki, paski, czapki, szaliki',
                'icon': 'fa-briefcase',
                'color': '#6c5ce7',
            },
            {
                'name': 'Odzież sportowa',
                'description': 'Ubrania i akcesoria sportowe',
                'icon': 'fa-person-running',
                'color': '#00cec9',
            },
            {
                'name': 'Mieszane',
                'description': 'Różne rodzaje odzieży',
                'icon': 'fa-shirt',
                'color': '#636e72',
            },
        ]
        
        for category_data in categories:
            cat, created = IncomingClothing.objects.update_or_create(
                name=category_data['name'],
                defaults=category_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category_data["name"]}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated category: {category_data["name"]}'))
    
    def create_initial_employees(self):
        # Create or update default employees with different colors
        employees = [
            {'name': 'Jan Kowalski', 'icon_color': '#4e73df'},  # Blue
            {'name': 'Anna Nowak', 'icon_color': '#e83e8c'},    # Pink
            {'name': 'Piotr Wiśniewski', 'icon_color': '#1cc88a'},  # Green
            {'name': 'Katarzyna Dąbrowska', 'icon_color': '#f6c23e'},  # Yellow
        ]
        
        for employee_data in employees:
            emp, created = Employee.objects.update_or_create(
                name=employee_data['name'],
                defaults=employee_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created employee: {employee_data["name"]}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated employee: {employee_data["name"]}'))