from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, F, Q
from django.db import models
from django.db.models.functions import TruncDate
from .models import Bag, Employee, SortedBag, SortedClothingCategory
from django import forms
from .forms import BagForm, BagSortForm, EmployeeForm, DateFilterForm, UserRegistrationForm, UserLoginForm, SortedBagForm, IncomingClothingForm, SortedClothingCategoryForm
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
import random
from datetime import datetime
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import IncomingClothing

# Form classes moved to forms.py

def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Rejestracja pomyślna! Jesteś teraz zalogowany.")
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'sortapp/register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Nieprawidłowy login lub hasło.")
    else:
        form = UserLoginForm()
    return render(request, 'sortapp/login.html', {'form': form})

def logout_user(request):
    logout(request)
    messages.success(request, "Wylogowano pomyślnie!")
    return redirect('login')

@login_required(login_url='login')
def home(request):
    # Liczba toreb, które wymagają sortowania
    unsorted_count = Bag.objects.filter(is_sorted=False).count()

    # Całkowita waga posortowana dzisiaj
    today = timezone.now().date()
    today_weight = Bag.objects.filter(
        is_sorted=True,
        sorted_at__date=today
    ).aggregate(total_weight=Sum('weight'))['total_weight'] or 0

    # Najlepszy sortownik dnia
    top_sorter = Employee.objects.filter(
        sorted_bags__is_sorted=True,
        sorted_bags__sorted_at__date=today
    ).annotate(
        total_sorted=Sum('sorted_bags__weight')
    ).order_by('-total_sorted').first()

    context = {
        'unsorted_count': unsorted_count,
        'today_weight': today_weight,
        'top_sorter': top_sorter,
    }
    return render(request, 'sortapp/home.html', context)

@login_required(login_url='login')
def register_bag(request):
    # Get all active clothing categories for the template
    clothing_categories = IncomingClothing.objects.filter(active=True)

    if request.method == 'POST':
        form = BagForm(request.POST)

        # Check if we received all required fields from the wizard
        has_clothing_type = request.POST.get('clothing_type', None)
        has_assigned_to = request.POST.get('assigned_to', None)
        has_weight = request.POST.get('weight', None)

        if not has_clothing_type or not has_assigned_to or not has_weight:
            messages.error(request, "Proszę wypełnić wszystkie pola formularza (kategoria, pracownik, waga).")
            return render(request, 'sortapp/register_bag.html', {
                'form': form,
                'clothing_categories': clothing_categories
            })

        if form.is_valid():
            bag = form.save(commit=False)
            # Set the current user as the author
            bag.author = request.user
            # Set author as prepared_by automatically
            bag.prepared_by = None

            # Always generate EAN in the background
            bag.generate_ean()
            bag.save()

            # Check if the "Save and Print" button was clicked
            if 'save_and_print' in request.POST:
                result = bag.send_to_printer()
                if result['success']:
                    messages.success(request, f"Worek zarejestrowany pomyślnie! Kod EAN {bag.bag_number} wysłany do drukarki.")
                else:
                    messages.warning(request, f"Worek zarejestrowany, ale drukowanie nie powiodło się: {result.get('message', 'Nieznany błąd')}")
            else:
                # "Just Save" button was clicked
                messages.success(request, f"Worek zarejestrowany pomyślnie! Kod EAN: {bag.bag_number}")

            return redirect('pending_bags')
        else:
            # Show the form with validation errors
            messages.error(request, "Proszę poprawić błędy w formularzu.")
    else:
        form = BagForm()

    return render(request, 'sortapp/register_bag.html', {
        'form': form,
        'clothing_categories': clothing_categories
    })

@login_required(login_url='login')
def sorted_bags(request):
    """
    Display a list of sorted bags (S-bags) with filter options.
    """
    # Get filter parameters
    date_filter = request.GET.get('date', None)
    category_filter = request.GET.get('category', None)
    employee_filter = request.GET.get('employee', None)
    
    # Start with all sorted bags
    sorted_bags_list = SortedBag.objects.all().order_by('-created_at')
    
    # Apply filters
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            sorted_bags_list = sorted_bags_list.filter(
                created_at__date=filter_date
            )
        except ValueError:
            # Invalid date format, ignore filter
            pass
    
    if category_filter and category_filter != 'all':
        sorted_bags_list = sorted_bags_list.filter(clothing_category_id=category_filter)
    
    if employee_filter and employee_filter != 'all':
        sorted_bags_list = sorted_bags_list.filter(prepared_by_id=employee_filter)
    
    # Get filter options for dropdowns
    categories = SortedClothingCategory.objects.filter(active=True)
    employees = Employee.objects.all()
    
    # Get date range for date picker
    today = timezone.now().date()
    date_range = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
    
    return render(request, 'sortapp/sorted_bags.html', {
        'sorted_bags': sorted_bags_list,
        'categories': categories,
        'employees': employees,
        'date_range': date_range,
        'selected_date': date_filter,
        'selected_category': category_filter,
        'selected_employee': employee_filter,
    })

@login_required(login_url='login')
def register_sorted_bag(request):
    sorted_categories = SortedClothingCategory.objects.filter(active=True)

    if request.method == 'POST':
        form = SortedBagForm(request.POST)
        if form.is_valid():
            sorted_bag = form.save(commit=False)
            sorted_bag.author = request.user
            sorted_bag.save()

            # Check if print_label is checked
            if form.cleaned_data.get('print_label'):
                # Send to printer
                print_result = sorted_bag.send_to_printer()
                if print_result['success']:
                    messages.success(request, f"Worek zarejestrowany pomyślnie! Etykieta wysłana do drukarki. Kod EAN: {sorted_bag.bag_number}")
                else:
                    messages.warning(request, f"Worek zarejestrowany, ale wystąpił problem z drukowaniem etykiety: {print_result['message']}")
            else:
                # "Just Save" button was clicked
                messages.success(request, f"Worek posortowanej odzieży zarejestrowany pomyślnie! Kod EAN: {sorted_bag.bag_number}")

            return redirect('home')
        else:
            # Show the form with validation errors
            messages.error(request, "Proszę poprawić błędy w formularzu.")
    else:
        form = SortedBagForm()

    return render(request, 'sortapp/register_sorted_bag.html', {
        'form': form,
        'sorted_categories': sorted_categories
    })

@login_required(login_url='login')
def pending_bags(request):
    bags = Bag.objects.filter(is_sorted=False).order_by('created_at')
    return render(request, 'sortapp/pending_bags.html', {'bags': bags})

def edit_pending_bag(request, bag_id):
    bag = Bag.objects.get(id=bag_id)
    if bag.is_sorted:
        messages.error(request, "Nie można edytować posortowanej torby.")
        return redirect('pending_bags')
    
    if request.method == 'POST':
        form = BagForm(request.POST, instance=bag)
        if form.is_valid():
            form.save()
            messages.success(request, f"Torba #{bag.bag_number} została zaktualizowana pomyślnie.")
            return redirect('pending_bags')
    else:
        form = BagForm(instance=bag)
        
    return render(request, 'sortapp/edit_pending_bag.html', {
        'form': form,
        'bag': bag,
        'clothing_categories': IncomingClothing.objects.filter(active=True)
    })

@login_required(login_url='login')
def mark_sorted(request, bag_id):
    bag = get_object_or_404(Bag, id=bag_id)

    if request.method == 'POST':
        form = BagSortForm(request.POST)
        if form.is_valid():
            # Verify that the bag has an assigned employee
            if not bag.assigned_to:
                messages.error(request, f"Nie można oznaczyć torby #{bag.bag_number} jako posortowanej, ponieważ nie przypisano do niej pracownika")
                return redirect('pending_bags')

            # Use the assigned employee instead of a separate sorted_by field
            bag.mark_as_sorted(bag.assigned_to)
            messages.success(request, f"Torba #{bag.bag_number} oznaczona jako posortowana przez {bag.assigned_to.name}")
            return redirect('pending_bags')
    else:
        form = BagSortForm()

    return render(request, 'sortapp/mark_sorted.html', {'bag': bag, 'form': form})

@login_required(login_url='login')
def update_sorted_bag(request, bag_id):
    """
    Update an existing sorted bag's details.
    """
    sorted_bag = get_object_or_404(SortedBag, id=bag_id)
    
    if request.method == 'POST':
        form = SortedBagForm(request.POST, instance=sorted_bag)
        if form.is_valid():
            form.save()
            messages.success(request, f"S-bag #{sorted_bag.bag_number} zaktualizowany pomyślnie!")
            return redirect('sorted_bags')
    else:
        form = SortedBagForm(instance=sorted_bag)
    
    return render(request, 'sortapp/update_sorted_bag.html', {
        'form': form,
        'bag': sorted_bag,
        'sorted_categories': SortedClothingCategory.objects.filter(active=True)
    })

@login_required(login_url='login')
def sorted_bag_stats(request):
    """
    Display statistics for sorted bags.
    """
    # Get filter parameters
    date_filter = request.GET.get('date', None)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            filter_date = timezone.now().date()
    else:
        filter_date = timezone.now().date()
    
    # Create form for date filtering
    form = DateFilterForm(initial={'date': filter_date})
    
    # Get all sorted bags for the selected date
    sorted_bags = SortedBag.objects.filter(
        created_at__date=filter_date
    )
    
    # Calculate total weight of sorted bags for the day
    total_weight = sorted_bags.aggregate(total=Sum('weight'))['total'] or 0
    
    # Get stats by employee
    employee_stats = sorted_bags.values(
        'prepared_by__name'
    ).annotate(
        total_sorted=Sum('weight'),
        bag_count=Count('id')
    ).filter(
        prepared_by__isnull=False
    ).order_by('-total_sorted')
    
    # Get stats by category
    category_stats = sorted_bags.values(
        'clothing_category__name',
        'clothing_category__color'
    ).annotate(
        total_weight=Sum('weight'),
        bag_count=Count('id')
    ).filter(
        clothing_category__isnull=False
    ).order_by('-total_weight')
    
    # Format date for display
    formatted_date = filter_date.strftime('%d.%m.%Y')
    
    return render(request, 'sortapp/sorted_bag_stats.html', {
        'form': form,
        'employee_stats': employee_stats,
        'category_stats': category_stats,
        'total_weight': total_weight,
        'current_date': formatted_date,
    })

@login_required(login_url='login')
def employee_stats(request):
    # Get date parameter or default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            stats_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            stats_date = timezone.now().date()
    else:
        stats_date = timezone.now().date()

    # Find all bags sorted on the selected date
    sorted_bags = Bag.objects.filter(
        is_sorted=True,
        sorted_at__date=stats_date
    )

    # Calculate average sorting time for each employee
    employee_sorting_times = {}
    for bag in sorted_bags:
        if bag.sorted_by_id not in employee_sorting_times:
            employee_sorting_times[bag.sorted_by_id] = {
                'total_seconds': 0,
                'bag_count': 0,
                'times': []
            }

        if bag.sorting_time:
            seconds = bag.sorting_time.total_seconds()
            employee_sorting_times[bag.sorted_by_id]['total_seconds'] += seconds
            employee_sorting_times[bag.sorted_by_id]['bag_count'] += 1
            employee_sorting_times[bag.sorted_by_id]['times'].append(seconds)

    # Get all employees with their sorting stats for the day
    employees = Employee.objects.annotate(
        bags_sorted=Count(
            'sorted_bags',
            filter=models.Q(sorted_bags__sorted_at__date=stats_date)
        ),
        total_weight=Sum(
            'sorted_bags__weight',
            filter=models.Q(sorted_bags__sorted_at__date=stats_date)
        )
    ).order_by('-total_weight')

    # Add sorting time data to each employee
    for employee in employees:
        if employee.id in employee_sorting_times:
            data = employee_sorting_times[employee.id]
            if data['bag_count'] > 0:
                # Average time in seconds
                employee.avg_sorting_time_seconds = data['total_seconds'] / data['bag_count']
                # Average time as formatted string (minutes:seconds)
                minutes = int(employee.avg_sorting_time_seconds // 60)
                seconds = int(employee.avg_sorting_time_seconds % 60)
                employee.avg_sorting_time = f"{minutes}:{seconds:02d}"
                # Sorting speed (kg per hour)
                if employee.total_weight and employee.avg_sorting_time_seconds > 0:
                    hours = employee.avg_sorting_time_seconds / 3600  # Convert seconds to hours
                    employee.sorting_speed = float(employee.total_weight) / (data['bag_count'] * hours)
                else:
                    employee.sorting_speed = 0
                # Fastest and slowest sorting times
                if data['times']:
                    employee.fastest_time_seconds = min(data['times'])
                    employee.slowest_time_seconds = max(data['times'])

                    fastest_minutes = int(employee.fastest_time_seconds // 60)
                    fastest_seconds = int(employee.fastest_time_seconds % 60)
                    employee.fastest_time = f"{fastest_minutes}:{fastest_seconds:02d}"

                    slowest_minutes = int(employee.slowest_time_seconds // 60)
                    slowest_seconds = int(employee.slowest_time_seconds % 60)
                    employee.slowest_time = f"{slowest_minutes}:{slowest_seconds:02d}"
            else:
                employee.avg_sorting_time_seconds = 0
                employee.avg_sorting_time = "0:00"
                employee.sorting_speed = 0
                employee.fastest_time = "0:00"
                employee.slowest_time = "0:00"
        else:
            employee.avg_sorting_time_seconds = 0
            employee.avg_sorting_time = "0:00"
            employee.sorting_speed = 0
            employee.fastest_time = "0:00"
            employee.slowest_time = "0:00"

    # Get previous and next dates that have data
    date_with_data = Bag.objects.filter(is_sorted=True).annotate(
        sort_date=TruncDate('sorted_at')
    ).values_list('sort_date', flat=True).distinct().order_by('sort_date')

    prev_date = None
    next_date = None

    date_list = list(date_with_data)
    if date_list:
        current_index = -1
        for i, date in enumerate(date_list):
            if date == stats_date:
                current_index = i
                break

        if current_index > 0:
            prev_date = date_list[current_index - 1]
        if current_index != -1 and current_index < len(date_list) - 1:
            next_date = date_list[current_index + 1]

    # Calculate overall average sorting time
    total_sorting_seconds = 0
    total_bags_with_time = 0
    for employee_id, data in employee_sorting_times.items():
        if data['bag_count'] > 0:
            total_sorting_seconds += data['total_seconds']
            total_bags_with_time += data['bag_count']

    avg_overall_time_seconds = 0
    if total_bags_with_time > 0:
        avg_overall_time_seconds = total_sorting_seconds / total_bags_with_time

    # Format for display
    avg_overall_minutes = int(avg_overall_time_seconds // 60)
    avg_overall_seconds = int(avg_overall_time_seconds % 60)
    avg_overall_time = f"{avg_overall_minutes}:{avg_overall_seconds:02d}"

    context = {
        'employees': employees,
        'stats_date': stats_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'avg_overall_time': avg_overall_time,
        'avg_overall_time_seconds': avg_overall_time_seconds,
    }
    return render(request, 'sortapp/employee_stats.html', context)

@login_required(login_url='login')
def generate_ean(request):
    """Generowanie unikalnego kodu EAN-13 i zwrócenie go jako JSON"""
    # Use current timestamp and random number to create a unique base
    timestamp = int(datetime.now().timestamp())
    random_part = random.randint(0, 999)

    # Create base number (12 digits - the 13th will be the check digit)
    base = str(timestamp)[-8:] + str(random_part).zfill(4)

    # Calculate check digit according to EAN-13 algorithm
    total = 0
    for i, digit in enumerate(base):
        if i % 2 == 0:  # even position (0-indexed)
            total += int(digit)
        else:  # odd position
            total += int(digit) * 3

    check_digit = (10 - (total % 10)) % 10

    # Combine base with check digit to form EAN-13
    ean = base + str(check_digit)

    # Check if this EAN already exists
    while Bag.objects.filter(bag_number=ean).exists():
        # If it exists, generate a new one
        random_part = random.randint(0, 999)
        base = str(timestamp)[-8:] + str(random_part).zfill(4)

        # Recalculate check digit
        total = 0
        for i, digit in enumerate(base):
            if i % 2 == 0:
                total += int(digit)
            else:
                total += int(digit) * 3

        check_digit = (10 - (total % 10)) % 10
        ean = base + str(check_digit)

    return JsonResponse({
        'success': True,
        'ean_code': ean,
        'message': 'Kod EAN wygenerowany pomyślnie'
    })

@login_required(login_url='login')
def employee_settings(request):
    """
    View for managing employees
    """
    employees = Employee.objects.all().order_by('name')
    
    context = {
        'employees': employees,
    }
    
    return render(request, 'sortapp/employee_settings.html', context)

@login_required(login_url='login')
def add_employee(request):
    """
    View for adding a new employee
    """
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pracownik został dodany pomyślnie.")
            return redirect('employee_settings')
    else:
        form = EmployeeForm()
    
    return render(request, 'sortapp/edit_employee.html', {
        'form': form,
        'title': 'Dodaj nowego pracownika',
        'action': 'Dodaj'
    })

@login_required(login_url='login')
def edit_employee(request, employee_id):
    """
    View for editing an existing employee
    """
    employee = get_object_or_404(Employee, id=employee_id)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Dane pracownika zostały zaktualizowane pomyślnie.")
            return redirect('employee_settings')
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'sortapp/edit_employee.html', {
        'form': form,
        'title': 'Edytuj dane pracownika',
        'action': 'Zapisz zmiany',
        'employee': employee
    })

@login_required(login_url='login')
def delete_employee(request, employee_id):
    """
    View for deleting an employee
    """
    employee = get_object_or_404(Employee, id=employee_id)
    
    # Check if the employee is referenced by any bags
    bags_with_employee = Bag.objects.filter(
        Q(prepared_by=employee) | Q(sorted_by=employee) | Q(assigned_to=employee)
    ).exists()
    
    sorted_bags_with_employee = SortedBag.objects.filter(prepared_by=employee).exists()
    
    if bags_with_employee or sorted_bags_with_employee:
        messages.error(request, "Nie można usunąć tego pracownika, ponieważ jest przypisany do worków w systemie.")
        return redirect('employee_settings')
    
    if request.method == 'POST':
        employee.delete()
        messages.success(request, "Pracownik został usunięty pomyślnie.")
        return redirect('employee_settings')
    
    return render(request, 'sortapp/delete_employee.html', {
        'employee': employee
    })

@login_required(login_url='login')
def settings(request):
    """
    Main settings view that lists all settings categories
    """
    employee_count = Employee.objects.count()
    incoming_category_count = IncomingClothing.objects.count()
    sorted_category_count = SortedClothingCategory.objects.count()
    
    context = {
        'employee_count': employee_count,
        'incoming_category_count': incoming_category_count,
        'sorted_category_count': sorted_category_count,
    }
    
    return render(request, 'sortapp/settings.html', context)

@login_required(login_url='login')
def category_settings(request):
    """
    View for managing all categories
    """
    incoming_categories = IncomingClothing.objects.all().order_by('name')
    sorted_categories = SortedClothingCategory.objects.all().order_by('name')
    
    context = {
        'incoming_categories': incoming_categories,
        'sorted_categories': sorted_categories,
    }
    
    return render(request, 'sortapp/category_settings.html', context)

@login_required(login_url='login')
def add_incoming_category(request):
    """
    View for adding a new incoming clothing category
    """
    if request.method == 'POST':
        form = IncomingClothingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Kategoria odzieży przychodzącej została dodana pomyślnie.")
            return redirect('category_settings')
    else:
        form = IncomingClothingForm()
    
    return render(request, 'sortapp/edit_category.html', {
        'form': form,
        'title': 'Dodaj nową kategorię odzieży przychodzącej',
        'action': 'Dodaj',
        'category_type': 'incoming'
    })

@login_required(login_url='login')
def edit_incoming_category(request, category_id):
    """
    View for editing an existing incoming clothing category
    """
    category = get_object_or_404(IncomingClothing, id=category_id)
    
    if request.method == 'POST':
        form = IncomingClothingForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Kategoria odzieży przychodzącej została zaktualizowana pomyślnie.")
            return redirect('category_settings')
    else:
        form = IncomingClothingForm(instance=category)
    
    return render(request, 'sortapp/edit_category.html', {
        'form': form,
        'title': 'Edytuj kategorię odzieży przychodzącej',
        'action': 'Zapisz zmiany',
        'category_type': 'incoming',
        'category': category
    })

@login_required(login_url='login')
def delete_incoming_category(request, category_id):
    """
    View for deleting an incoming clothing category
    """
    category = get_object_or_404(IncomingClothing, id=category_id)
    
    # Check if the category is in use
    if Bag.objects.filter(clothing_type=category).exists():
        messages.error(request, "Nie można usunąć tej kategorii, ponieważ jest używana przez worki w systemie.")
        return redirect('category_settings')
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Kategoria odzieży przychodzącej została usunięta pomyślnie.")
        return redirect('category_settings')
    
    return render(request, 'sortapp/delete_category.html', {
        'category': category,
        'category_type': 'incoming'
    })

@login_required(login_url='login')
def add_sorted_category(request):
    """
    View for adding a new sorted clothing category
    """
    if request.method == 'POST':
        form = SortedClothingCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Kategoria posortowanej odzieży została dodana pomyślnie.")
            return redirect('category_settings')
    else:
        form = SortedClothingCategoryForm()
    
    return render(request, 'sortapp/edit_category.html', {
        'form': form,
        'title': 'Dodaj nową kategorię posortowanej odzieży',
        'action': 'Dodaj',
        'category_type': 'sorted'
    })

@login_required(login_url='login')
def edit_sorted_category(request, category_id):
    """
    View for editing an existing sorted clothing category
    """
    category = get_object_or_404(SortedClothingCategory, id=category_id)
    
    if request.method == 'POST':
        form = SortedClothingCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Kategoria posortowanej odzieży została zaktualizowana pomyślnie.")
            return redirect('category_settings')
    else:
        form = SortedClothingCategoryForm(instance=category)
    
    return render(request, 'sortapp/edit_category.html', {
        'form': form,
        'title': 'Edytuj kategorię posortowanej odzieży',
        'action': 'Zapisz zmiany',
        'category_type': 'sorted',
        'category': category
    })

@login_required(login_url='login')
def delete_sorted_category(request, category_id):
    """
    View for deleting a sorted clothing category
    """
    category = get_object_or_404(SortedClothingCategory, id=category_id)
    
    # Check if the category is in use
    if SortedBag.objects.filter(clothing_category=category).exists():
        messages.error(request, "Nie można usunąć tej kategorii, ponieważ jest używana przez posortowane worki w systemie.")
        return redirect('category_settings')
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Kategoria posortowanej odzieży została usunięta pomyślnie.")
        return redirect('category_settings')
    
    return render(request, 'sortapp/delete_category.html', {
        'category': category,
        'category_type': 'sorted'
    })
