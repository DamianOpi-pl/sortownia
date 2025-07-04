from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, F, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
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
from django.urls import reverse
from django.utils.timesince import timesince

# Form classes moved to forms.py

def get_polish_date(date_obj):
    """Format date in Polish format (weekday, day month year)"""
    polish_weekdays = {
        0: 'poniedziałek',
        1: 'wtorek',
        2: 'środa',
        3: 'czwartek',
        4: 'piątek',
        5: 'sobota',
        6: 'niedziela',
    }
    polish_months = {
        1: 'stycznia',
        2: 'lutego',
        3: 'marca',
        4: 'kwietnia',
        5: 'maja',
        6: 'czerwca',
        7: 'lipca',
        8: 'sierpnia',
        9: 'września',
        10: 'października',
        11: 'listopada',
        12: 'grudnia',
    }
    weekday = polish_weekdays[date_obj.weekday()]
    return f"{weekday}, {date_obj.day} {polish_months[date_obj.month]} {date_obj.year}"

def format_time_difference(start_time, end_time):
    """Format time difference between two datetime objects in a human-readable format"""
    if not start_time or not end_time:
        return None
        
    delta = end_time - start_time
    total_minutes = delta.total_seconds() // 60
    
    if total_minutes < 60:
        return f"{int(total_minutes)} min"
    else:
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        return f"{hours} godz {minutes} min"

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
    
    # Liczba zamkniętych (posortowanych) toreb
    closed_count = Bag.objects.filter(is_sorted=True).count()

    # Statystyki dla dzisiaj
    today = timezone.now().date()
    today_stats = Bag.objects.filter(
        is_sorted=True,
        sorted_at__date=today
    ).aggregate(
        total_weight=Sum('weight'),
        bags_count=Count('id')
    )
    
    today_weight = today_stats['total_weight'] or 0
    today_closed_count = today_stats['bags_count'] or 0

    # Najlepszy sortownik dnia
    top_sorter = Employee.objects.filter(
        sorted_bags__is_sorted=True,
        sorted_bags__sorted_at__date=today
    ).annotate(
        total_sorted=Sum('sorted_bags__weight')
    ).order_by('-total_sorted').first()

    context = {
        'unsorted_count': unsorted_count,
        'closed_count': closed_count,
        'today_weight': today_weight,
        'today_closed_count': today_closed_count,
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
            
            # Check if the employee already has active bags assigned
            assigned_employee = bag.assigned_to
            if assigned_employee:
                active_bags = Bag.objects.filter(
                    assigned_to=assigned_employee,
                    is_sorted=False
                ).exclude(id=bag.id if bag.id else 0)  # Exclude current bag if it exists
                
                # Close any active bags for this employee
                if active_bags.exists():
                    now = timezone.now()
                    for active_bag in active_bags:
                        active_bag.is_sorted = True
                        active_bag.sorted_by = active_bag.assigned_to
                        active_bag.sorted_at = now
                        active_bag.save()
                        messages.info(
                            request, 
                            f"Automatycznie zamknięto wcześniej przydzielony worek #{active_bag.bag_number} dla {assigned_employee.name}"
                        )

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
    status_filter = request.GET.get('status', None)
    
    # Get current date in Polish format
    today = timezone.now().date()
    current_date_polish = get_polish_date(today)

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

    if status_filter:
        if status_filter == 'open':
            sorted_bags_list = sorted_bags_list.filter(is_closed=False)
        elif status_filter == 'closed':
            sorted_bags_list = sorted_bags_list.filter(is_closed=True)

    # Get filter options for dropdowns
    categories = SortedClothingCategory.objects.filter(active=True)
    employees = Employee.objects.all()

    # Get date range for date picker
    today = timezone.now().date()
    date_range = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]

    # Pagination
    paginator = Paginator(sorted_bags_list, 6)  # Show 6 bags per page (2 rows of 3)
    page_number = request.GET.get('page', 1)
    try:
        bags_page = paginator.page(page_number)
    except PageNotAnInteger:
        bags_page = paginator.page(1)
    except EmptyPage:
        bags_page = paginator.page(paginator.num_pages)
        
    # Build filter definitions for template
    filters = [
        {
            'name': 'date',
            'label': 'Data',
            'type': 'select',
            'col_size': 3,
            'options': [
                {'value': '', 'label': 'Wszystkie daty', 'selected': not date_filter}
            ] + [
                {'value': date, 'label': date, 'selected': date_filter == date}
                for date in date_range
            ]
        },
        {
            'name': 'category',
            'label': 'Kategoria',
            'type': 'select',
            'col_size': 3,
            'options': [
                {'value': 'all', 'label': 'Wszystkie kategorie', 'selected': category_filter != 'all' and not category_filter}
            ] + [
                {'value': str(cat.id), 'label': cat.name, 'selected': category_filter == str(cat.id)}
                for cat in categories
            ]
        },
        {
            'name': 'employee',
            'label': 'Pracownik',
            'type': 'select',
            'col_size': 3,
            'options': [
                {'value': 'all', 'label': 'Wszyscy pracownicy', 'selected': employee_filter != 'all' and not employee_filter}
            ] + [
                {'value': str(emp.id), 'label': emp.name, 'selected': employee_filter == str(emp.id)}
                for emp in employees
            ]
        },
        {
            'name': 'status',
            'label': 'Status',
            'type': 'select',
            'col_size': 3,
            'options': [
                {'value': 'all', 'label': 'Wszystkie torby', 'selected': status_filter != 'all' and not status_filter},
                {'value': 'open', 'label': 'Otwarte', 'selected': status_filter == 'open'},
                {'value': 'closed', 'label': 'Zamknięte', 'selected': status_filter == 'closed'}
            ]
        }
    ]
    
    # Pagination query parameters
    pagination_params = ""
    if date_filter:
        pagination_params += f"&date={date_filter}"
    if category_filter and category_filter != 'all':
        pagination_params += f"&category={category_filter}"
    if employee_filter and employee_filter != 'all':
        pagination_params += f"&employee={employee_filter}"
    if status_filter and status_filter != 'all':
        pagination_params += f"&status={status_filter}"
    
    # Prepare data for template
    processed_bags = []
    for bag in bags_page:
        # Determine status color and icon
        if bag.is_closed:
            status_color = "#6c757d"  # gray
            status_icon = "fas fa-lock"
            status_text = "Zamknięta"
            if bag.closed_at:
                status_text += f" ({bag.closed_at.strftime('%d.%m.%Y')})"
        else:
            status_color = "#6bb907"  # S-bag green
            status_icon = "fas fa-unlock"
            status_text = "Otwarta"
            
        processed_bag = {
            'id': bag.id,
            'bag_number': bag.bag_number,
            'weight': bag.weight,
            'employee_name': bag.prepared_by.name if bag.prepared_by else None,
            'employee_color': bag.prepared_by.icon_color if bag.prepared_by else "#333",
            'no_employee_text': 'Nie przypisano',
            'date_display': bag.created_at.strftime("%d.%m.%Y %H:%M") if bag.created_at else "",
            'detail_url': reverse('update_sorted_bag', args=[bag.id]),
            'show_category': True,
            'category': bag.clothing_category,
            'status_display': status_text,
            'status_color': status_color,
            'status_icon': status_icon,
            'actions': [
                {
                    'type': 'link',
                    'url': reverse('update_sorted_bag', args=[bag.id]),
                    'icon': 'fas fa-info-circle',
                    'class': 'info-button'
                },
                {
                    'type': 'link',
                    'url': reverse('sorted_bag_weight_history', args=[bag.id]),
                    'icon': 'fas fa-history',
                    'class': 'print-button'
                }
            ]
        }
        processed_bags.append(processed_bag)
    
    # Determine empty state message
    if date_filter or (category_filter and category_filter != 'all') or (employee_filter and employee_filter != 'all') or (status_filter and status_filter != 'all'):
        empty_message = "Brak worków pasujących do wybranych filtrów."
        empty_button_text = "Wyczyść filtry"
        empty_button_url = reverse('sorted_bags')
        empty_button_icon = "fas fa-filter"
    else:
        empty_message = "Nie zarejestrowano jeszcze żadnych posortowanych worków."
        empty_button_text = "Dodaj nowy worek"
        empty_button_url = reverse('register_sorted_bag')
        empty_button_icon = "fas fa-plus-circle"
    
    context = {
        'title': 'Posortowane worki (S-bags) - Sortownia Odzieży',
        'heading': 'Worki posortowane (S-bags)',
        'icon_class': 'fa-tags',
        'accent_color': '6bb907',  # S-bag color
        'accent_rgb': '107, 185, 7',
        'cards_per_row': 2,  # 2 larger cards per row
        'show_filter_button': True,
        'add_url': 'register_sorted_bag',
        'current_url': 'sorted_bags',
        'bags': processed_bags,
        'filters': filters,
        'pagination_query_params': pagination_params,
        'empty_title': 'Brak posortowanych worków',
        'empty_message': empty_message,
        'empty_button_text': empty_button_text,
        'empty_button_url': empty_button_url,
        'empty_button_icon': empty_button_icon,
        'show_instructions': False
    }
    
    # Pass the page object for pagination
    context['bags_page'] = bags_page
    
    return render(request, 'sortapp/bag_list_template.html', context)

@login_required(login_url='login')
def register_sorted_bag(request):
    sorted_categories = SortedClothingCategory.objects.filter(active=True)

    # Check if there are any active categories
    if not sorted_categories.exists():
        messages.error(request, "Nie można utworzyć posortowanej torby, ponieważ nie ma aktywnych kategorii. Skontaktuj się z administratorem.")
        return redirect('home')

    if request.method == 'POST':
        form = SortedBagForm(request.POST)
        if form.is_valid():
            try:
                sorted_bag = form.save(commit=False)
                sorted_bag.author = request.user

                # Ensure category is properly set from form data
                category = form.cleaned_data.get('clothing_category')
                if category:
                    # Already an object from cleaned_data, no need to re-fetch
                    sorted_bag.clothing_category = category
                else:
                    # This should not happen due to form validation, but just in case
                    messages.error(request, "Proszę wybrać kategorię posortowanej odzieży.")
                    return render(request, 'sortapp/register_sorted_bag.html', {'form': form, 'sorted_categories': sorted_categories})

                # Check if close_bag is checked
                if form.cleaned_data.get('close_bag'):
                    sorted_bag.is_closed = True
                    sorted_bag.closed_at = timezone.now()

                # Save the bag first to get an ID
                sorted_bag.save()

                # Create initial weight history record
                from .models import SortedBagWeightHistory
                SortedBagWeightHistory.objects.create(
                    sorted_bag=sorted_bag,
                    previous_weight=sorted_bag.weight,
                    new_weight=sorted_bag.weight,
                    changed_by=request.user,
                    notes="Initial weight at creation"
                )

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
                    status = "zamknięty" if sorted_bag.is_closed else "zarejestrowany"
                    messages.success(request, f"Worek posortowanej odzieży {status} pomyślnie! Kod EAN: {sorted_bag.bag_number}")

                return redirect('home')

            except Exception as e:
                # Log the error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving sorted bag: {str(e)}")

                # Show error message to user
                messages.error(request, f"Wystąpił błąd podczas zapisywania torby: {str(e)}")
                return render(request, 'sortapp/register_sorted_bag.html', {'form': form, 'sorted_categories': sorted_categories})
        else:
            # Get all form errors
            all_errors = []
            for field, errors in form.errors.items():
                field_name = form[field].label or field
                for error in errors:
                    all_errors.append(f"{field_name}: {error}")

            # Show the form with validation errors
            error_message = "Proszę poprawić błędy w formularzu: " + ", ".join(all_errors)
            messages.error(request, error_message)
    else:
        form = SortedBagForm()
        # Pre-select the first category if there's at least one available
        if sorted_categories.exists():
            form.initial['clothing_category'] = sorted_categories.first().id

    # Return the form with context
    return render(request, 'sortapp/register_sorted_bag.html', {
        'form': form,
        'sorted_categories': sorted_categories
    })

@login_required(login_url='login')
def pending_bags(request):
    """
    Display a list of pending bags (N-bags) that haven't been sorted yet.
    """
    # Get all pending bags
    bag_queryset = Bag.objects.filter(is_sorted=False).order_by('created_at')
    
    # Pagination
    paginator = Paginator(bag_queryset, 12)  # Show 12 bags per page
    page_number = request.GET.get('page', 1)
    try:
        bags_page = paginator.page(page_number)
    except PageNotAnInteger:
        bags_page = paginator.page(1)
    except EmptyPage:
        bags_page = paginator.page(paginator.num_pages)
    
    # Prepare data for template
    processed_bags = []
    for bag in bags_page:
        processed_bag = {
            'id': bag.id,
            'bag_number': bag.bag_number,
            'weight': bag.weight,
            'employee_name': bag.assigned_to.name if bag.assigned_to else None,
            'employee_color': bag.assigned_to.icon_color if bag.assigned_to else "#333",
            'no_employee_text': 'Nie przydzielono',
            'date_display': bag.created_at.strftime("%d.%m.%Y %H:%M") if bag.created_at else "",
            'detail_url': reverse('bag_detail', args=[bag.id]),
            'show_category': True,
            'category': bag.clothing_type,
            'time_display': f"{timesince(bag.created_at)} temu" if bag.created_at else None,
            'time_icon': 'fas fa-history',
            'actions': [
                {
                    'type': 'link',
                    'url': reverse('bag_detail', args=[bag.id]),
                    'icon': 'fas fa-info-circle',
                    'class': 'info-button'
                },
                {
                    'type': 'link',
                    'url': reverse('mark_sorted', args=[bag.id]),
                    'icon': 'fas fa-check',
                    'class': 'check-button'
                },
                {
                    'type': 'link',
                    'url': reverse('edit_pending_bag', args=[bag.id]),
                    'icon': 'fas fa-edit',
                    'class': 'edit-button'
                },
                {
                    'type': 'button',
                    'icon': 'fas fa-print',
                    'class': 'print-button print-ean-btn',
                    'data_attr': 'data-ean',
                    'data_value': bag.bag_number
                }
            ]
        }
        processed_bags.append(processed_bag)
    
    # Get current date in Polish format
    today = timezone.now().date()
    current_date_polish = get_polish_date(today)
    
    # Prepare instruction content
    instruction_content = f"""
        <p>Aby oznaczyć worek jako posortowany ({current_date_polish}):</p>
        <ol>
            <li>Wybierz worek z powyższej listy</li>
            <li>Naciśnij zielony przycisk <i class="fas fa-check"></i> lub przejdź do szczegółów worka</li>
            <li>Wybierz pracownika, który wykonał sortowanie</li>
            <li>Wyślij formularz, aby zarejestrować ukończenie</li>
        </ol>
        <p class="mb-0 text-muted">System automatycznie obliczy czas.</p>
    """
    
    context = {
        'title': 'Oczekujące worki - Sortownia Odzieży',
        'heading': 'Worki oczekujące na sortowanie',
        'icon_class': 'fa-clock',
        'accent_color': 'b96b07',  # N-bag color
        'accent_rgb': '185, 107, 7',
        'cards_per_row': 3,
        'show_filter_button': False,
        'add_url': 'register_bag',
        'current_url': 'pending_bags',
        'bags': processed_bags,
        'pagination_query_params': '',
        'empty_title': 'Brak oczekujących worków',
        'empty_message': 'Wszystkie worki zostały posortowane lub nie zarejestrowano jeszcze żadnych.',
        'empty_button_text': 'Zarejestruj nowy worek (N-bag)',
        'empty_button_url': reverse('register_bag'),
        'empty_button_icon': 'fas fa-plus-circle',
        'show_instructions': True,
        'instruction_title': 'Instrukcje sortowania',
        'instruction_content': instruction_content
    }
    
    # Pass the page object for pagination
    context['bags_page'] = bags_page
    
    return render(request, 'sortapp/bag_list_template.html', context)

def closed_bags(request):
    """
    Display a list of closed (sorted) N-bags.
    """
    # Get filter parameters
    date_filter = request.GET.get('date', None)
    category_filter = request.GET.get('category', None)
    employee_filter = request.GET.get('employee', None)
    
    # Get current date in Polish format
    today = timezone.now().date()
    current_date_polish = get_polish_date(today)
    
    # Start with all closed bags
    bag_queryset = Bag.objects.filter(is_sorted=True).order_by('-sorted_at')
    
    # Apply date filter if provided
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            bag_queryset = bag_queryset.filter(sorted_at__date=filter_date)
        except ValueError:
            messages.warning(request, "Nieprawidłowy format daty. Wyświetlam wszystkie zamknięte worki.")
    
    # Apply category filter if provided
    if category_filter:
        bag_queryset = bag_queryset.filter(clothing_type_id=category_filter)
    
    # Apply employee filter if provided
    if employee_filter:
        bag_queryset = bag_queryset.filter(sorted_by_id=employee_filter)
    
    # Pagination
    paginator = Paginator(bag_queryset, 12)  # Show 12 bags per page
    page_number = request.GET.get('page', 1)
    try:
        bags_page = paginator.page(page_number)
    except PageNotAnInteger:
        bags_page = paginator.page(1)
    except EmptyPage:
        bags_page = paginator.page(paginator.num_pages)
    
    # Get unique categories and employees for the filter dropdowns
    categories = IncomingClothing.objects.filter(active=True)
    employees = Employee.objects.all()
    
    # Build filter definitions for template
    filters = [
        {
            'name': 'date',
            'label': 'Data sortowania',
            'type': 'date',
            'value': date_filter,
            'col_size': 4
        },
        {
            'name': 'category',
            'label': 'Kategoria odzieży',
            'type': 'select',
            'col_size': 4,
            'options': [
                {'value': '', 'label': 'Wszystkie kategorie', 'selected': not category_filter}
            ] + [
                {'value': cat.id, 'label': cat.name, 'selected': category_filter == str(cat.id)}
                for cat in categories
            ]
        },
        {
            'name': 'employee',
            'label': 'Posortowane przez',
            'type': 'select',
            'col_size': 4,
            'options': [
                {'value': '', 'label': 'Wszyscy pracownicy', 'selected': not employee_filter}
            ] + [
                {'value': emp.id, 'label': emp.name, 'selected': employee_filter == str(emp.id)}
                for emp in employees
            ]
        }
    ]
    
    # Pagination query parameters
    pagination_params = ""
    if date_filter:
        pagination_params += f"&date={date_filter}"
    if category_filter:
        pagination_params += f"&category={category_filter}"
    if employee_filter:
        pagination_params += f"&employee={employee_filter}"
    
    # Prepare data for template
    processed_bags = []
    for bag in bags_page:
        processed_bag = {
            'id': bag.id,
            'bag_number': bag.bag_number,
            'weight': bag.weight,
            'employee_name': bag.sorted_by.name if bag.sorted_by else None,
            'employee_color': bag.sorted_by.icon_color if bag.sorted_by else "#333",
            'no_employee_text': 'Brak informacji',
            'date_display': bag.sorted_at.strftime("%d.%m.%Y %H:%M") if bag.sorted_at else bag.created_at.strftime("%d.%m.%Y %H:%M"),
            'detail_url': reverse('bag_detail', args=[bag.id]) + (f"?return_to=closed_bags{pagination_params}" if pagination_params else ""),
            'show_category': True,
            'category': bag.clothing_type,
            'time_display': format_time_difference(bag.created_at, bag.sorted_at) if bag.sorted_at else None,
            'time_icon': 'fas fa-hourglass-end',
            'actions': [
                {
                    'type': 'link',
                    'url': reverse('bag_detail', args=[bag.id]) + (f"?return_to=closed_bags{pagination_params}" if pagination_params else ""),
                    'icon': 'fas fa-info-circle',
                    'class': 'info-button'
                },
                {
                    'type': 'button',
                    'icon': 'fas fa-print',
                    'class': 'print-button print-ean-btn',
                    'data_attr': 'data-ean',
                    'data_value': bag.bag_number
                }
            ]
        }
        processed_bags.append(processed_bag)
    
    # Determine empty state message
    if date_filter or category_filter or employee_filter:
        empty_message = "Brak worków pasujących do wybranych filtrów."
        empty_button_text = "Wyczyść filtry"
        empty_button_url = reverse('closed_bags')
        empty_button_icon = "fas fa-filter"
    else:
        empty_message = "Żaden worek nie został jeszcze posortowany."
        empty_button_text = "Zobacz oczekujące worki"
        empty_button_url = reverse('pending_bags')
        empty_button_icon = "fas fa-list"
    
    context = {
        'title': 'Zamknięte worki - Sortownia Odzieży',
        'heading': 'Worki posortowane',
        'icon_class': 'fa-check-circle',
        'accent_color': 'b96b07',  # N-bag color
        'accent_rgb': '185, 107, 7',
        'cards_per_row': 3,
        'show_filter_button': True,
        'add_url': None,
        'current_url': 'closed_bags',
        'bags': processed_bags,
        'filters': filters,
        'pagination_query_params': pagination_params,
        'empty_title': 'Brak posortowanych worków',
        'empty_message': empty_message,
        'empty_button_text': empty_button_text,
        'empty_button_url': empty_button_url,
        'empty_button_icon': empty_button_icon,
        'show_instructions': False
    }
    
    # Pass the page object for pagination
    context['bags_page'] = bags_page
    
    return render(request, 'sortapp/bag_list_template.html', context)


def bag_detail(request, bag_id):
    bag = get_object_or_404(Bag, id=bag_id)
    return render(request, 'sortapp/bag_detail.html', {'bag': bag})

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
    try:
        sorted_bag = get_object_or_404(SortedBag, id=bag_id)

        # If the bag is already closed, redirect to the list with a message
        if sorted_bag.is_closed:
            messages.warning(request, f"S-bag #{sorted_bag.bag_number} jest już zamknięty i nie może być edytowany.")
            return redirect('sorted_bags')

        if request.method == 'POST':
            form = SortedBagForm(request.POST, instance=sorted_bag)
            if form.is_valid():
                try:
                    # Store the old weight before updating
                    old_weight = sorted_bag.weight
                    new_weight = form.cleaned_data.get('weight')
                    weight_changed = old_weight != new_weight

                    sorted_bag = form.save(commit=False)

                    # Ensure category is properly set from form data
                    category = form.cleaned_data.get('clothing_category')
                    if category:
                        # Already an object from cleaned_data, no need to re-fetch
                        sorted_bag.clothing_category = category
                    else:
                        raise ValueError("Kategoria odzieży jest wymagana")

                    # Check if close_bag is checked
                    if form.cleaned_data.get('close_bag'):
                        sorted_bag.is_closed = True
                        sorted_bag.closed_at = timezone.now()
                        closing_msg = " i zamknięty"
                    else:
                        closing_msg = ""

                    # Pass the user to be captured in weight history through save() method
                    sorted_bag.save(user=request.user)

                    # If the bag is being closed and the weight didn't change, we need to manually
                    # create a final weight history entry as the save() method won't detect a change
                    if form.cleaned_data.get('close_bag') and not weight_changed:
                        from .models import SortedBagWeightHistory
                        SortedBagWeightHistory.objects.create(
                            sorted_bag=sorted_bag,
                            previous_weight=sorted_bag.weight,
                            new_weight=sorted_bag.weight,
                            changed_by=request.user,
                            is_final=True,
                            notes="Torba zamknięta"
                        )
                    messages.success(request, f"S-bag #{sorted_bag.bag_number} zaktualizowany{closing_msg} pomyślnie!")
                    return redirect('sorted_bags')
                except Exception as e:
                    # Log the error
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error updating sorted bag {bag_id}: {str(e)}")

                    # Show error message to user
                    messages.error(request, f"Wystąpił błąd podczas aktualizacji torby: {str(e)}")
            else:
                # Get all form errors
                all_errors = []
                for field, errors in form.errors.items():
                    field_name = form[field].label or field
                    for error in errors:
                        all_errors.append(f"{field_name}: {error}")

                # Show the form with validation errors
                error_message = "Proszę poprawić błędy w formularzu: " + ", ".join(all_errors)
                messages.error(request, error_message)
        else:
            form = SortedBagForm(instance=sorted_bag)

        # Make sure we have active categories
        sorted_categories = SortedClothingCategory.objects.filter(active=True)
        if not sorted_categories.exists():
            messages.warning(request, "Uwaga: Nie ma aktywnych kategorii odzieży. Skontaktuj się z administratorem.")

        return render(request, 'sortapp/update_sorted_bag.html', {
            'form': form,
            'bag': sorted_bag,
            'sorted_categories': sorted_categories
        })
    except Exception as e:
        # Handle any unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in update_sorted_bag view for bag {bag_id}: {str(e)}")

        messages.error(request, f"Wystąpił nieoczekiwany błąd: {str(e)}")
        return redirect('sorted_bags')

@login_required(login_url='login')
def sorted_bag_weight_history(request, bag_id):
    """
    Display the weight history for a specific sorted bag.
    """
    sorted_bag = get_object_or_404(SortedBag, id=bag_id)
    weight_history = sorted_bag.weight_history.all().order_by('-changed_at')

    return render(request, 'sortapp/sorted_bag_weight_history.html', {
        'bag': sorted_bag,
        'weight_history': weight_history
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

    # Use database aggregation to calculate sorting statistics
    # This avoids loading all bags into memory
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

    # Create a more efficient query to get sorting time data
    from django.db.models import F, ExpressionWrapper, fields
    from django.db.models.functions import Extract

    # Get all bags for the day with calculated sorting time
    sorted_bags_with_times = Bag.objects.filter(
        is_sorted=True,
        sorted_at__date=stats_date
    ).annotate(
        sorting_seconds=ExpressionWrapper(
            Extract(F('sorted_at') - F('created_at'), 'epoch'),
            output_field=fields.FloatField()
        )
    ).values('sorted_by', 'sorting_seconds', 'weight')

    # Use a dictionary to hold employee data for efficient lookup
    employee_data = {}
    
    # Calculate overall stats variables
    total_sorting_seconds = 0
    total_bags_with_time = 0
    
    # Process all bags in a single pass
    for bag in sorted_bags_with_times:
        employee_id = bag['sorted_by']
        seconds = bag['sorting_seconds']
        
        if seconds is not None and seconds > 0:
            if employee_id not in employee_data:
                employee_data[employee_id] = {
                    'total_seconds': 0,
                    'bag_count': 0,
                    'times': [],
                }
            
            employee_data[employee_id]['total_seconds'] += seconds
            employee_data[employee_id]['bag_count'] += 1
            employee_data[employee_id]['times'].append(seconds)
            
            # Add to overall totals
            total_sorting_seconds += seconds
            total_bags_with_time += 1

    # Efficiently calculate previous and next dates
    date_with_data = Bag.objects.filter(is_sorted=True).annotate(
        sort_date=TruncDate('sorted_at')
    ).values('sort_date').distinct().order_by('sort_date')
    
    # Get only the dates needed (before and after the current date)
    prev_date_query = date_with_data.filter(sort_date__lt=stats_date).order_by('-sort_date').first()
    next_date_query = date_with_data.filter(sort_date__gt=stats_date).order_by('sort_date').first()
    
    prev_date = prev_date_query['sort_date'] if prev_date_query else None
    next_date = next_date_query['sort_date'] if next_date_query else None

    # Calculate overall average sorting time
    avg_overall_time_seconds = 0
    if total_bags_with_time > 0:
        avg_overall_time_seconds = total_sorting_seconds / total_bags_with_time

    # Format for display
    avg_overall_minutes = int(avg_overall_time_seconds // 60)
    avg_overall_seconds = int(avg_overall_time_seconds % 60)
    avg_overall_time = f"{avg_overall_minutes}:{avg_overall_seconds:02d}"

    # Add calculated data to each employee object
    for employee in employees:
        if employee.id in employee_data:
            data = employee_data[employee.id]
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
