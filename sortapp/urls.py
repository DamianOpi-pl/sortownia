from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_bag, name='register_bag'),
    path('register-sorted/', views.register_sorted_bag, name='register_sorted_bag'),
    path('sorted-bags/', views.sorted_bags, name='sorted_bags'),
    path('sorted-bags/update/<int:bag_id>/', views.update_sorted_bag, name='update_sorted_bag'),
    path('sorted-bags/stats/', views.sorted_bag_stats, name='sorted_bag_stats'),
    path('pending/', views.pending_bags, name='pending_bags'),
    path('pending/edit/<int:bag_id>/', views.edit_pending_bag, name='edit_pending_bag'),
    path('mark-sorted/<int:bag_id>/', views.mark_sorted, name='mark_sorted'),
    path('stats/', views.employee_stats, name='employee_stats'),
    path('generate-ean/', views.generate_ean, name='generate_ean'),
    # Authentication URLs
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register-user/', views.register_user, name='register_user'),
    
    # Settings URLs
    path('settings/', views.settings, name='settings'),
    path('settings/categories/', views.category_settings, name='category_settings'),
    
    # Incoming Categories
    path('settings/categories/incoming/add/', views.add_incoming_category, name='add_incoming_category'),
    path('settings/categories/incoming/edit/<int:category_id>/', views.edit_incoming_category, name='edit_incoming_category'),
    path('settings/categories/incoming/delete/<int:category_id>/', views.delete_incoming_category, name='delete_incoming_category'),
    
    # Sorted Categories
    path('settings/categories/sorted/add/', views.add_sorted_category, name='add_sorted_category'),
    path('settings/categories/sorted/edit/<int:category_id>/', views.edit_sorted_category, name='edit_sorted_category'),
    path('settings/categories/sorted/delete/<int:category_id>/', views.delete_sorted_category, name='delete_sorted_category'),
    
    # Employees management
    path('settings/employees/', views.employee_settings, name='employee_settings'),
    path('settings/employees/add/', views.add_employee, name='add_employee'),
    path('settings/employees/edit/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('settings/employees/delete/<int:employee_id>/', views.delete_employee, name='delete_employee'),
]