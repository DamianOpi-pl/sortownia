from django.contrib import admin
from .models import Employee, Bag, IncomingClothing, SortedClothingCategory, SortedBag

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_color')
    search_fields = ('name',)

    def get_list_display(self, request):
        return ('name', 'icon_color')

    def get_list_display_links(self, request, list_display):
        return ('name',)

    def get_list_filter(self, request):
        return ()

    def get_search_fields(self, request):
        return ('name',)

    def get_readonly_fields(self, request, obj=None):
        return ('icon_color',)

    def get_model_perms(self, request):
        perms = super().get_model_perms(request)
        return perms

    def get_verbose_name(self):
        return "Pracownik"

    def get_verbose_name_plural(self):
        return "Pracownicy"

@admin.register(Bag)
class BagAdmin(admin.ModelAdmin):
    list_display = ('bag_number', 'weight', 'is_sorted', 'sorted_by', 'created_at', 'sorted_at')
    list_filter = ('is_sorted', 'sorted_by', 'created_at', 'sorted_at')
    search_fields = ('bag_number',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'sorted_at')

    def get_verbose_name(self):
        return "Torba"

    def get_verbose_name_plural(self):
        return "Torby"

    def get_list_display(self, request):
        return ('bag_number', 'weight', 'is_sorted', 'sorted_by', 'created_at', 'sorted_at')

    def get_list_filter(self, request):
        return ('is_sorted', 'sorted_by', 'created_at', 'sorted_at')

    def get_search_fields(self, request):
        return ('bag_number',)

    def get_readonly_fields(self, request, obj=None):
        return ('created_at', 'sorted_at')

    def get_date_hierarchy(self):
        return 'created_at'

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ('Informacje podstawowe', {
                'fields': ('bag_number', 'weight', 'prepared_by', 'clothing_type', 'assigned_to')
            }),
            ('Informacje o sortowaniu', {
                'fields': ('is_sorted', 'sorted_by', 'sorted_at')
            }),
            ('Dane czasowe', {
                'fields': ('created_at',)
            }),
            ('Dane użytkownika', {
                'fields': ('author',)
            }),
        ]
        return fieldsets

@admin.register(IncomingClothing)
class IncomingClothingAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'icon', 'color')
    list_filter = ('active',)
    search_fields = ('name', 'description')
    
    fieldsets = [
        ('Podstawowe informacje', {
            'fields': ('name', 'description', 'active')
        }),
        ('Wygląd', {
            'fields': ('icon', 'color'),
            'description': 'Ustaw ikonę Font Awesome (np. fa-tshirt) i kolor tła (format HEX, np. #3498db)'
        })
    ]

@admin.register(SortedClothingCategory)
class SortedClothingCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'icon', 'color')
    list_filter = ('active',)
    search_fields = ('name', 'description')
    
    fieldsets = [
        ('Podstawowe informacje', {
            'fields': ('name', 'description', 'active')
        }),
        ('Wygląd', {
            'fields': ('icon', 'color'),
            'description': 'Ustaw ikonę Font Awesome (np. fa-tshirt) i kolor tła (format HEX, np. #3498db)'
        })
    ]

@admin.register(SortedBag)
class SortedBagAdmin(admin.ModelAdmin):
    list_display = ('bag_number', 'weight', 'clothing_category', 'prepared_by', 'created_at')
    list_filter = ('clothing_category', 'prepared_by', 'created_at')
    search_fields = ('bag_number',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    
    fieldsets = [
        ('Informacje podstawowe', {
            'fields': ('bag_number', 'weight', 'clothing_category', 'prepared_by')
        }),
        ('Powiązania', {
            'fields': ('original_bag',)
        }),
        ('Dane czasowe', {
            'fields': ('created_at',)
        }),
        ('Dane użytkownika', {
            'fields': ('author',)
        }),
    ]
