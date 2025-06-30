from django.core.management.base import BaseCommand
from sortapp.models import Employee

class Command(BaseCommand):
    help = 'Sets unique colors for all employees in the system'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Setting employee colors...'))
        
        # Define a list of attractive colors for employee icons
        colors = [
            '#4e73df',  # Blue
            '#e83e8c',  # Pink
            '#1cc88a',  # Green
            '#f6c23e',  # Yellow
            '#fd7e14',  # Orange
            '#6f42c1',  # Purple
            '#20c9a6',  # Teal
            '#36b9cc',  # Cyan
            '#5a5c69',  # Gray
            '#e74a3b',  # Red
            '#2c9faf',  # Light Blue
            '#f39c12',  # Amber
            '#3498db',  # Primary Blue
            '#2ecc71',  # Emerald
            '#9b59b6',  # Amethyst
            '#e67e22'   # Carrot
        ]
        
        # Get all employees
        employees = Employee.objects.all()
        
        # Update each employee with a color
        for i, employee in enumerate(employees):
            color_index = i % len(colors)
            employee.icon_color = colors[color_index]
            employee.save()
            
            # Print output
            self.stdout.write(
                self.style.SUCCESS(f'Updated employee: {employee.name} with color: {employee.icon_color}')
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {employees.count()} employees with unique colors!'))