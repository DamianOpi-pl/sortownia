from django import template
from decimal import Decimal
from datetime import datetime
import re

register = template.Library()

@register.filter
def first(value):
    """Returns the first character of a string"""
    if value and isinstance(value, str) and len(value) > 0:
        return value[0]
    return ""

@register.filter
def sum_attr(queryset, attr_name):
    """Sums a specified attribute across all objects in a queryset"""
    if not queryset:
        return 0
    
    total = 0
    for obj in queryset:
        value = getattr(obj, attr_name, 0) or 0
        total += value
    
    return total

@register.filter
def div(value, arg):
    """Divides the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def sub(value, arg):
    """Subtracts the argument from the value"""
    try:
        return float(value) - float(arg)
    except ValueError:
        return 0

@register.filter
def percentage(value, total):
    """Returns the value as a percentage of the total"""
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def polish_date(date_obj, format_str=None):
    """Formats the date in Polish style"""
    if not date_obj:
        return ""
    
    if not isinstance(date_obj, datetime):
        try:
            date_obj = datetime.strptime(str(date_obj), "%Y-%m-%d")
        except ValueError:
            return date_obj
    
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
    
    polish_weekdays = {
        0: 'poniedziałek',
        1: 'wtorek',
        2: 'środa',
        3: 'czwartek',
        4: 'piątek',
        5: 'sobota',
        6: 'niedziela',
    }
    
    if format_str == 'long':
        weekday = polish_weekdays[date_obj.weekday()]
        return f"{weekday}, {date_obj.day} {polish_months[date_obj.month]} {date_obj.year}"
    elif format_str == 'short':
        return f"{date_obj.day}.{date_obj.month}.{date_obj.year}"
    else:
        return f"{date_obj.day} {polish_months[date_obj.month]} {date_obj.year}"

@register.filter
def polish_pluralize(value, forms):
    """
    Returns the appropriate Polish plural form based on the number value.
    
    Usage: {{ count|polish_pluralize:"torba,torby,toreb" }}
    
    The three forms correspond to Polish grammar rules:
    - First form for singular (1)
    - Second form for numbers ending in 2-4 (except 12-14)
    - Third form for other numbers
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return ''
    
    forms = forms.split(',')
    if len(forms) < 3:
        return ''
    
    if value == 1:
        return forms[0]  # First form (singular)
    
    # Special case for 12-14
    if 12 <= value % 100 <= 14:
        return forms[2]  # Third form
    
    # For 2-4, except 12-14
    if 2 <= value % 10 <= 4:
        return forms[1]  # Second form
    
    # Other cases
    return forms[2]  # Third form
    
@register.filter
def format_weight(value):
    """Format weight value with proper Polish decimal separator"""
    if not value:
        return "0,00 kg"
    
    try:
        value_str = str(float(value)).replace('.', ',')
        # Ensure two decimal places
        if ',' in value_str:
            main_part, decimal_part = value_str.split(',')
            if len(decimal_part) == 1:
                value_str = f"{main_part},{decimal_part}0"
            elif len(decimal_part) > 2:
                value_str = f"{main_part},{decimal_part[:2]}"
        else:
            value_str = f"{value_str},00"
        
        return f"{value_str} kg"
    except (ValueError, TypeError):
        return f"{value} kg"
        
@register.filter
def format_time(seconds):
    """Format time in seconds to a human-readable format (minutes:seconds or hours:minutes:seconds)"""
    if not seconds:
        return "0:00"
    
    try:
        seconds = float(seconds)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    except (ValueError, TypeError):
        return str(seconds)

@register.filter
def timedelta(start_date, end_date):
    """
    Calculate and format the time difference between two dates in a human-readable format.
    Usage: {{ start_date|timedelta:end_date }}
    Returns: "X godz Y min" or "X min" format
    """
    if not start_date or not end_date:
        return "brak danych"
    
    try:
        # Ensure we're working with datetime objects
        if not isinstance(start_date, datetime):
            start_date = datetime.strptime(str(start_date), "%Y-%m-%d %H:%M:%S")
        if not isinstance(end_date, datetime):
            end_date = datetime.strptime(str(end_date), "%Y-%m-%d %H:%M:%S")
        
        # Calculate the time difference
        delta = end_date - start_date
        
        # Convert to hours and minutes
        total_seconds = delta.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        # Format the output
        if hours > 0:
            return f"{hours} godz {minutes} min"
        else:
            return f"{minutes} min"
    except (ValueError, TypeError):
        return "brak danych"