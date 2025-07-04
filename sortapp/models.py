from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Employee(models.Model):
    name = models.CharField(max_length=100, verbose_name="Imię i nazwisko")
    icon_color = models.CharField(max_length=20, default="#3498db", help_text="Kolor ikony pracownika w formacie HEX, np. '#3498db'", verbose_name="Kolor ikony")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Pracownik"
        verbose_name_plural = "Pracownicy"

class IncomingClothing(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nazwa kategorii")
    description = models.TextField(blank=True, verbose_name="Opis")
    icon = models.CharField(max_length=50, blank=True, help_text="Klasa ikony Font Awesome, np. 'fa-tshirt'", verbose_name="Ikona")
    color = models.CharField(max_length=20, default="#3498db", help_text="Kolor w formacie HEX, np. '#3498db'", verbose_name="Kolor")
    active = models.BooleanField(default=True, verbose_name="Aktywna")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Odzież przychodząca"
        verbose_name_plural = "Odzież przychodząca"
        ordering = ['name']


class SortedClothingCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nazwa kategorii")
    description = models.TextField(blank=True, verbose_name="Opis")
    icon = models.CharField(max_length=50, blank=True, help_text="Klasa ikony Font Awesome, np. 'fa-tshirt'", verbose_name="Ikona")
    color = models.CharField(max_length=20, default="#3498db", help_text="Kolor w formacie HEX, np. '#3498db'", verbose_name="Kolor")
    active = models.BooleanField(default=True, verbose_name="Aktywna")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kategoria posortowanej odzieży"
        verbose_name_plural = "Kategorie posortowanej odzieży"
        ordering = ['name']

class Bag(models.Model):
    bag_number = models.CharField(max_length=50, unique=True, help_text="Unikalny identyfikator torby (taki sam jak kod EAN)", verbose_name="Numer torby")
    weight = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Waga w kilogramach", verbose_name="Waga")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Data utworzenia", db_index=True)
    sorted_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='sorted_bags', verbose_name="Posortowane przez", db_index=True)
    sorted_at = models.DateTimeField(null=True, blank=True, verbose_name="Data sortowania", db_index=True)
    is_sorted = models.BooleanField(default=False, verbose_name="Posortowane", db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bags', verbose_name="Autor", null=True)
    clothing_type = models.ForeignKey(IncomingClothing, on_delete=models.PROTECT, related_name='bags', verbose_name="Rodzaj odzieży", null=True, blank=True)
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_bags', verbose_name="Przydzielone do")

    def __str__(self):
        return f"Torba #{self.bag_number} - {self.weight}kg"
        
    @property
    def efficiency_kg_per_hour(self):
        """Calculate sorting efficiency in kg per hour"""
        if not self.is_sorted or not self.sorted_at:
            return 0
            
        # Calculate time difference in hours
        time_diff = (self.sorted_at - self.created_at).total_seconds() / 3600
        
        # Avoid division by zero
        if time_diff <= 0:
            return 0
            
        # Calculate and round to 2 decimal places
        efficiency = float(self.weight) / time_diff
        return round(efficiency, 2)

    def mark_as_sorted(self, employee=None):
        # If no employee is specified, use the assigned employee
        if employee is None and self.assigned_to:
            employee = self.assigned_to

        self.sorted_by = employee
        self.sorted_at = timezone.now()
        self.is_sorted = True
        self.save()

    @property
    def sorting_time(self):
        if self.is_sorted and self.sorted_at:
            return self.sorted_at - self.created_at
        return None

    def generate_ean(self):
        """Generuje unikalny kod EAN-13 dla tej torby"""
        import random
        from datetime import datetime

        # Używa aktualnego znacznika czasu i losowej liczby do utworzenia unikalnej podstawy
        timestamp = int(datetime.now().timestamp())
        random_part = random.randint(0, 999)

        # Tworzy podstawową liczbę (12 cyfr - 13-ta będzie cyfrą kontrolną)
        base = str(timestamp)[-8:] + str(random_part).zfill(4)

        # Oblicza cyfrę kontrolną według algorytmu EAN-13
        total = 0
        for i, digit in enumerate(base):
            if i % 2 == 0:  # pozycja parzysta (indeksowana od 0)
                total += int(digit)
            else:  # pozycja nieparzysta
                total += int(digit) * 3

        check_digit = (10 - (total % 10)) % 10

        # Łączy podstawę z cyfrą kontrolną, aby utworzyć EAN-13
        ean = base + str(check_digit)

        # Używa EAN jako numeru torby
        self.bag_number = ean
        self.save()
        return ean

    def send_to_printer(self):
        """Wysyła numer torby/kod EAN do drukarki etykiet"""
        # Upewniamy się, że mamy kod EAN przed wydrukiem
        if not self.bag_number:
            return {
                'success': False,
                'message': "Brak kodu EAN do wydrukowania"
            }

        # To jest symbol zastępczy dla rzeczywistej integracji z drukarką
        # W prawdziwej aplikacji należałoby zintegrować się z API drukarki
        # Na przykład, używając cups, brother_ql lub innej biblioteki drukarki

        # Dla celów demonstracyjnych, po prostu zwrócimy sukces
        return {
            'success': True,
            'ean_code': self.bag_number,
            'message': f"Kod EAN {self.bag_number} wysłany do drukarki"
        }


class SortedBag(models.Model):
    bag_number = models.CharField(max_length=50, unique=True, help_text="Unikalny identyfikator torby (taki sam jak kod EAN)", verbose_name="Numer torby", blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Waga w kilogramach", verbose_name="Waga")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Data utworzenia", db_index=True)
    prepared_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='prepared_sorted_bags', verbose_name="Przygotowane przez", null=True, blank=True, db_index=True)
    clothing_category = models.ForeignKey(SortedClothingCategory, on_delete=models.PROTECT, related_name='sorted_bags', verbose_name="Kategoria odzieży", null=True, blank=False, db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sorted_bags', verbose_name="Autor", null=True)
    original_bag = models.ForeignKey(Bag, on_delete=models.SET_NULL, related_name='resulting_sorted_bags', verbose_name="Worek źródłowy", null=True, blank=True)
    is_closed = models.BooleanField(default=False, verbose_name="Zamknięty", db_index=True)
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="Data zamknięcia", db_index=True)

    def __str__(self):
        category_name = self.clothing_category.name if self.clothing_category else "Brak kategorii"
        return f"S-Torba #{self.bag_number} - {self.weight}kg - {category_name}"

    def save(self, *args, **kwargs):
        # Check if this is an update (not a new bag) and the weight has changed
        if self.pk is not None:
            try:
                old_instance = SortedBag.objects.get(pk=self.pk)
                if old_instance.weight != self.weight:
                    # Create a history record when weight changes
                    SortedBagWeightHistory.objects.create(
                        sorted_bag=self,
                        previous_weight=old_instance.weight,
                        new_weight=self.weight,
                        changed_by=kwargs.pop('user', None) if 'user' in kwargs else None
                    )
            except SortedBag.DoesNotExist:
                pass

        # If there's no bag number yet, generate one before saving
        if not self.bag_number:
            self.generate_ean()

        # Ensure the clothing_category is set
        if not self.clothing_category:
            from django.core.exceptions import ValidationError
            raise ValidationError("Kategoria odzieży jest wymagana")

        super(SortedBag, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Posortowana torba"
        verbose_name_plural = "Posortowane torby"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at', 'clothing_category']),
            models.Index(fields=['prepared_by', 'created_at']),
        ]

    def generate_ean(self):
        """Generuje unikalny kod EAN-13 dla tej torby"""
        import random
        from datetime import datetime

        # Używa aktualnego znacznika czasu i losowej liczby do utworzenia unikalnej podstawy
        timestamp = int(datetime.now().timestamp())
        random_part = random.randint(0, 999)

        # Tworzy podstawową liczbę (12 cyfr - 13-ta będzie cyfrą kontrolną)
        base = str(timestamp)[-8:] + str(random_part).zfill(4)

        # Oblicza cyfrę kontrolną według algorytmu EAN-13
        total = 0
        for i, digit in enumerate(base):
            if i % 2 == 0:  # pozycja parzysta (indeksowana od 0)
                total += int(digit)
            else:  # pozycja nieparzysta
                total += int(digit) * 3

        check_digit = (10 - (total % 10)) % 10

        # Łączy podstawę z cyfrą kontrolną, aby utworzyć EAN-13
        ean = base + str(check_digit)

        # Używa EAN jako numeru torby i dodaje prefiks "S-" dla posortowanych toreb
        self.bag_number = f"S-{ean}"

        # Check if this EAN already exists to avoid unique constraint violations
        from django.db.models import Q
        if SortedBag.objects.filter(Q(bag_number=self.bag_number) & ~Q(pk=self.pk if self.pk else -1)).exists():
            # If it exists, try again with a different random number
            return self.generate_ean()

        return self.bag_number

    def send_to_printer(self):
        """Wysyła numer torby/kod EAN do drukarki etykiet"""
        # Upewniamy się, że mamy kod EAN przed wydrukiem
        if not self.bag_number:
            return {
                'success': False,
                'message': "Brak kodu EAN do wydrukowania"
            }

        # Dla celów demonstracyjnych, po prostu zwrócimy sukces
        return {
            'success': True,
            'ean_code': self.bag_number,
            'message': f"Kod EAN {self.bag_number} wysłany do drukarki"
        }

    def close(self, user=None):
        """Zamyka torbę, uniemożliwiając dalsze edycje"""
        if not self.is_closed:
            self.is_closed = True
            self.closed_at = timezone.now()

            # Create a final weight history entry when closing the bag
            SortedBagWeightHistory.objects.create(
                sorted_bag=self,
                previous_weight=self.weight,
                new_weight=self.weight,
                changed_by=user,
                is_final=True,
                notes="Torba zamknięta"
            )

            self.save()
            return True
        return False


class SortedBagWeightHistory(models.Model):
    """Track weight changes for sorted bags"""
    sorted_bag = models.ForeignKey(SortedBag, on_delete=models.CASCADE, related_name='weight_history', verbose_name="Posortowana torba", db_index=True)
    previous_weight = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Poprzednia waga")
    new_weight = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Nowa waga")
    changed_at = models.DateTimeField(default=timezone.now, verbose_name="Data zmiany", db_index=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='weight_changes', verbose_name="Zmienione przez")
    is_final = models.BooleanField(default=False, verbose_name="Finalna waga", db_index=True)
    notes = models.CharField(max_length=255, blank=True, null=True, verbose_name="Uwagi")

    class Meta:
        verbose_name = "Historia wagi torby"
        verbose_name_plural = "Historia wag toreb"
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['sorted_bag', 'changed_at']),
        ]

    def __str__(self):
        return f"{self.sorted_bag.bag_number}: {self.previous_weight}kg → {self.new_weight}kg ({self.changed_at.strftime('%d.%m.%Y %H:%M')})"
