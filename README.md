# Clothing Sorting System

A Django web application for managing clothing sorting operations in a warehouse or recycling facility.

## Overview

This application helps track the workflow of a clothing sorting company:

1. An employee prepares a bag of clothes for sorting and places it on a stand
2. The bag is registered in the system with a bag number, weight, and the name of the employee who prepared it
3. After sorting, the bag is marked as completed by the sorting employee
4. The system tracks performance statistics, showing daily scores (in kg) for each sorter

## Features

- Registration of new bags for sorting
- Tracking of pending bags that need sorting
- Completion tracking when bags are sorted
- Employee performance statistics by date
- Dashboard with key metrics and summaries

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run migrations to create the database:
   ```
   python manage.py migrate
   ```
5. Create a superuser to access the admin panel:
   ```
   python manage.py createsuperuser
   ```
6. Start the development server:
   ```
   python manage.py runserver
   ```
7. Access the application at http://127.0.0.1:8000/

## Initial Setup

Before using the application, you'll need to create employee records:

1. Access the admin panel at http://127.0.0.1:8000/admin/
2. Log in with the superuser credentials created during installation
3. Add employees through the admin interface
4. Return to the main application and start registering bags

## Usage

### Registering a Bag

1. Click on "Register Bag" in the navigation menu
2. Enter the bag number, weight, and select the employee who prepared it
3. Submit the form to register the bag

### Marking a Bag as Sorted

1. Go to "Pending Bags" in the navigation menu
2. Find the bag you want to mark as sorted
3. Click "Mark as Sorted"
4. Select the employee who performed the sorting
5. Submit the form to complete the process

### Viewing Statistics

1. Navigate to "Statistics" in the menu
2. View the daily performance of all employees
3. Use the date selector to view statistics for different days

## Technologies Used

- Django 5.2
- Bootstrap 5.3
- Chart.js for visualizations
- SQLite database (can be configured for other databases)

## License

This project is licensed under the MIT License - see the LICENSE file for details.