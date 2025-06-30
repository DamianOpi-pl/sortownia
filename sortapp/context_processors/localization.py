from datetime import datetime

def polish_localization(request):
    """
    Context processor that adds Polish localization data to the context.
    """
    # Polish month names in genitive form (for use with date display)
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
    
    # Polish month names in nominative form
    polish_months_nominative = {
        1: 'styczeń',
        2: 'luty',
        3: 'marzec',
        4: 'kwiecień',
        5: 'maj',
        6: 'czerwiec',
        7: 'lipiec',
        8: 'sierpień',
        9: 'wrzesień',
        10: 'październik',
        11: 'listopad',
        12: 'grudzień',
    }
    
    # Polish weekday names
    polish_weekdays = {
        0: 'poniedziałek',
        1: 'wtorek',
        2: 'środa',
        3: 'czwartek',
        4: 'piątek',
        5: 'sobota',
        6: 'niedziela',
    }
    
    # Current date in Polish format
    now = datetime.now()
    current_date_polish = f"{now.day} {polish_months[now.month]} {now.year}"
    
    return {
        'polish_months': polish_months,
        'polish_months_nominative': polish_months_nominative,
        'polish_weekdays': polish_weekdays,
        'current_date_polish': current_date_polish,
    }