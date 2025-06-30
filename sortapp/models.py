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
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Data utworzenia")
    prepared_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='prepared_bags', verbose_name="Przygotowane przez", null=True, blank=True)
    sorted_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='sorted_bags', verbose_name="Posortowane przez")
    sorted_at = models.DateTimeField(null=True, blank=True, verbose_name="Data sortowania")
    is_sorted = models.BooleanField(default=False, verbose_name="Posortowane")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bags', verbose_name="Autor", null=True)
    clothing_type = models.ForeignKey(IncomingClothing, on_delete=models.PROTECT, related_name='bags', verbose_name="Rodzaj odzieży", null=True, blank=True)
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_bags', verbose_name="Przydzielone do")

    def __str__(self):
        return f"Torba #{self.bag_number} - {self.weight}kg"

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
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Data utworzenia")
    prepared_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='prepared_sorted_bags', verbose_name="Przygotowane przez", null=True, blank=True)
    clothing_category = models.ForeignKey(SortedClothingCategory, on_delete=models.PROTECT, related_name='sorted_bags', verbose_name="Kategoria odzieży", null=True, blank=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sorted_bags', verbose_name="Autor", null=True)
    original_bag = models.ForeignKey(Bag, on_delete=models.SET_NULL, related_name='resulting_sorted_bags', verbose_name="Worek źródłowy", null=True, blank=True)

    def __str__(self):
        return f"S-Torba #{self.bag_number} - {self.weight}kg - {self.clothing_category.name}"

    class Meta:
        verbose_name = "Posortowana torba"
        verbose_name_plural = "Posortowane torby"
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        # If there's no bag number yet, generate one before saving
        if not self.bag_number:
            self.generate_ean()
        super(SortedBag, self).save(*args, **kwargs)
        
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
