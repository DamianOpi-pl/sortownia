from django import forms
from django.utils.safestring import mark_safe
from .models import Bag, Employee, IncomingClothing, SortedBag, SortedClothingCategory
from django.core.validators import RegexValidator
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class BagForm(forms.ModelForm):
    print_label = forms.BooleanField(
        required=False,
        initial=False,
        label='Drukuj etykietę',
        help_text='Wyślij kod EAN do drukarki etykiet',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Bag
        fields = ['weight', 'clothing_type', 'assigned_to']
        widgets = {
            'weight': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'inputmode': 'numeric', 'pattern': '[0-9]*', 'placeholder': 'Waga (kg)'}),
            'clothing_type': forms.RadioSelect(attrs={'class': 'category-radio'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control form-control-lg'}),
        }
        labels = {
            'weight': 'Waga (kg)',
            'clothing_type': 'Rodzaj odzieży',
            'assigned_to': 'Przydzielone do sortowania przez',
        }
        help_texts = {
            'weight': 'Waga torby w kilogramach (liczba całkowita)',
            'clothing_type': 'Wybierz kategorię odzieży w worku',
            'assigned_to': 'Pracownik, który będzie sortował worek',
        }




    def __init__(self, *args, **kwargs):
        super(BagForm, self).__init__(*args, **kwargs)
        self.fields['clothing_type'].queryset = IncomingClothing.objects.filter(active=True)

        # Set up employee choices with initials
        employees = Employee.objects.all()
        choices = [('', 'Pracownik, który będzie sortował worek')]

        for employee in employees:
            # Get initials for the icon
            initials = ''.join([name[0] for name in employee.name.split() if name])
            if not initials:
                initials = '?'
                
            # Create HTML with initials and name below
            employee_html = f'''
            <div style="text-align: center;">
                <div style="width: 50px; height: 50px; margin: 0 auto; background-color: {employee.icon_color}; color: white; 
                     border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.5rem;">
                    {initials}
                </div>
                <div style="margin-top: 5px; font-size: 0.9rem;">{employee.name}</div>
            </div>
            '''
            choices.append((employee.id, mark_safe(employee_html)))
        
        self.fields['assigned_to'].choices = choices
        
    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        # Allow whole numbers (integers)
        return weight

class BagSortForm(forms.Form):
    # Empty form as the field is no longer needed
    pass


class SortedBagForm(forms.ModelForm):
    print_label = forms.BooleanField(
        required=False,
        initial=False,
        label='Drukuj etykietę',
        help_text='Wyślij kod EAN do drukarki etykiet',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = SortedBag
        fields = ['weight', 'clothing_category', 'prepared_by', 'original_bag']
        widgets = {
            'weight': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'inputmode': 'numeric', 'pattern': '[0-9]*', 'placeholder': 'Waga (kg)'}),
            'clothing_category': forms.RadioSelect(attrs={'class': 'category-radio'}),
            'prepared_by': forms.Select(attrs={'class': 'form-control form-control-lg'}),
            'original_bag': forms.Select(attrs={'class': 'form-control form-control-lg'})
        }
        labels = {
            'weight': 'Waga (kg)',
            'clothing_category': 'Kategoria posortowanej odzieży',
            'prepared_by': 'Przygotowane przez',
            'original_bag': 'Worek źródłowy (opcjonalnie)'
        }
        help_texts = {
            'weight': 'Waga torby w kilogramach (liczba całkowita)',
            'clothing_category': 'Wybierz kategorię posortowanej odzieży',
            'prepared_by': 'Pracownik, który przygotował torbę',
            'original_bag': 'Wybierz worek źródłowy (N-bag), z którego powstała ta torba'
        }
        
    def __init__(self, *args, **kwargs):
        super(SortedBagForm, self).__init__(*args, **kwargs)
        self.fields['clothing_category'].queryset = SortedClothingCategory.objects.filter(active=True)
        self.fields['original_bag'].queryset = Bag.objects.filter(is_sorted=True)
        self.fields['original_bag'].required = False
        
        # Set up employee choices with initials for prepared_by
        employees = Employee.objects.all()
        choices = [('', 'Wybierz pracownika')]
        
        for employee in employees:
            # Get initials for the icon
            initials = ''.join([name[0] for name in employee.name.split() if name])
            if not initials:
                initials = '?'
                
            # Create HTML with initials and name below
            employee_html = f'''
            <div style="text-align: center;">
                <div style="width: 50px; height: 50px; margin: 0 auto; background-color: {employee.icon_color}; color: white; 
                     border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.5rem;">
                    {initials}
                </div>
                <div style="margin-top: 5px; font-size: 0.9rem;">{employee.name}</div>
            </div>
            '''
            choices.append((employee.id, mark_safe(employee_html)))
        
        self.fields['prepared_by'].choices = choices
        
    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        # Allow whole numbers (integers)
        return weight

class EmployeeForm(forms.ModelForm):
    hex_color_validator = RegexValidator(
        regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
        message='Kolor musi być w formacie HEX, np. #3498db'
    )
    
    icon_color = forms.CharField(
        validators=[hex_color_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'color'
        })
    )
    
    class Meta:
        model = Employee
        fields = ['name', 'icon_color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wprowadź imię i nazwisko pracownika'})
        }
        labels = {
            'name': 'Imię i nazwisko pracownika',
            'icon_color': 'Kolor ikony'
        }
        help_texts = {
            'icon_color': 'Kolor ikony pracownika (używany w interfejsie aplikacji)',
        }

class DateFilterForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False,
        label='Wybierz datę'
    )

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nazwa użytkownika'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Hasło'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Powtórz hasło'})

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nazwa użytkownika'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Hasło'})
    )

class IncomingClothingForm(forms.ModelForm):
    hex_color_validator = RegexValidator(
        regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
        message='Kolor musi być w formacie HEX, np. #3498db'
    )
    
    color = forms.CharField(
        validators=[hex_color_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'color'
        })
    )
    
    class Meta:
        model = IncomingClothing
        fields = ['name', 'description', 'icon', 'color', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nazwa kategorii'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Opis kategorii'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Klasa ikony Font Awesome, np. fa-tshirt'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class SortedClothingCategoryForm(forms.ModelForm):
    hex_color_validator = RegexValidator(
        regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
        message='Kolor musi być w formacie HEX, np. #3498db'
    )
    
    color = forms.CharField(
        validators=[hex_color_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'color'
        })
    )
    
    class Meta:
        model = SortedClothingCategory
        fields = ['name', 'description', 'icon', 'color', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nazwa kategorii'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Opis kategorii'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Klasa ikony Font Awesome, np. fa-tshirt'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
