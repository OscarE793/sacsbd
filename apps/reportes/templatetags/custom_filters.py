from django import template
from django.utils.safestring import mark_safe
import math

register = template.Library()


@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def filesizeformat_custom(bytes_value):
    """
    Format the value like Django's filesizeformat but with Spanish units
    """
    try:
        bytes_value = float(bytes_value)
    except (TypeError, ValueError, UnicodeDecodeError):
        return "0 bytes"

    if bytes_value < 1024:
        return f"{bytes_value:.0f} bytes"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.1f} KB"
    elif bytes_value < 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.1f} MB"
    elif bytes_value < 1024 * 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
    else:
        return f"{bytes_value / (1024 * 1024 * 1024 * 1024):.1f} TB"


@register.filter
def status_badge_class(status):
    """
    Return appropriate badge class for status
    """
    status_classes = {
        'Online': 'badge-success',
        'Offline': 'badge-danger', 
        'Restoring': 'badge-warning',
        'Recovering': 'badge-warning',
        'Suspect': 'badge-danger',
        'Emergency': 'badge-danger',
        'Succeeded': 'badge-success',
        'Failed': 'badge-danger',
        'Retry': 'badge-warning',
        'Canceled': 'badge-secondary',
        'Compliant': 'badge-success',
        'Warning': 'badge-warning',
        'Critical': 'badge-danger'
    }
    return status_classes.get(status, 'badge-secondary')


@register.filter
def compliance_indicator_class(status):
    """
    Return appropriate indicator class for compliance status
    """
    indicator_classes = {
        'Compliant': 'indicator-compliant',
        'Warning': 'indicator-warning', 
        'Critical': 'indicator-critical'
    }
    return indicator_classes.get(status, 'indicator-secondary')


@register.filter
def backup_type_badge(backup_type):
    """
    Return appropriate badge for backup type
    """
    type_badges = {
        'D': '<span class="badge badge-light-primary">Completo</span>',
        'I': '<span class="badge badge-light-info">Diferencial</span>',
        'L': '<span class="badge badge-light-warning">Log</span>'
    }
    return mark_safe(type_badges.get(backup_type, '<span class="badge badge-light-secondary">Otro</span>'))


@register.filter
def hours_badge_class(hours):
    """
    Return appropriate badge class based on hours since backup
    """
    try:
        hours = int(hours)
        if hours < 24:
            return 'badge-success'
        elif hours < 168:  # 7 days
            return 'badge-warning'
        else:
            return 'badge-danger'
    except (ValueError, TypeError):
        return 'badge-secondary'


@register.filter
def format_duration(seconds):
    """
    Format duration in seconds to HH:MM:SS
    """
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except (ValueError, TypeError):
        return "00:00:00"


@register.filter
def percentage(value, total):
    """
    Calculate percentage
    """
    try:
        value = float(value)
        total = float(total)
        if total == 0:
            return 0
        return round((value / total) * 100, 1)
    except (ValueError, TypeError):
        return 0


@register.filter
def progress_width(count):
    """
    Calculate progress bar width based on backup count
    """
    try:
        count = int(count)
        if count > 10:
            return 100
        elif count > 5:
            return min(count * 10, 100)
        else:
            return max(count * 20, 10)
    except (ValueError, TypeError):
        return 10


@register.filter
def progress_class(count):
    """
    Return progress bar class based on backup count
    """
    try:
        count = int(count)
        if count > 10:
            return 'bg-success'
        elif count > 5:
            return 'bg-warning'
        else:
            return 'bg-danger'
    except (ValueError, TypeError):
        return 'bg-secondary'


@register.simple_tag
def query_params(request, **kwargs):
    """
    Update query parameters while preserving existing ones
    """
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value:
            params[key] = value
        elif key in params:
            del params[key]
    return params.urlencode()


@register.inclusion_tag('reportes/includes/status_indicator.html')
def status_indicator(status, size='sm'):
    """
    Render status indicator component
    """
    return {
        'status': status,
        'size': size,
        'class': status_badge_class(status)
    }


@register.inclusion_tag('reportes/includes/backup_progress.html')
def backup_progress(count, max_count=20):
    """
    Render backup progress component
    """
    try:
        count = int(count)
        max_count = int(max_count)
        percentage = min((count / max_count) * 100, 100) if max_count > 0 else 0
    except (ValueError, TypeError):
        count = 0
        percentage = 0
    
    return {
        'count': count,
        'percentage': percentage,
        'class': progress_class(count)
    }


@register.filter
def truncate_path(path, length=50):
    """
    Truncate file path smartly
    """
    if not path or len(path) <= length:
        return path
    
    # Try to keep filename and show beginning of path
    parts = path.split('\\')
    if len(parts) > 1:
        filename = parts[-1]
        if len(filename) < length - 10:
            remaining_length = length - len(filename) - 5  # 5 for "...\"
            truncated_path = path[:remaining_length] + "...\\" + filename
            return truncated_path
    
    return path[:length-3] + "..."


@register.filter
def format_sql_date(date_value):
    """
    Format SQL Server date values
    """
    if not date_value:
        return "-"
    
    try:
        # If it's already a datetime object
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%d/%m/%Y %H:%M')
        
        # If it's a string, try to parse it
        from datetime import datetime
        if isinstance(date_value, str):
            # Handle different SQL Server date formats
            formats = [
                '%Y%m%d',           # YYYYMMDD
                '%Y-%m-%d',         # YYYY-MM-DD
                '%Y-%m-%d %H:%M:%S', # YYYY-MM-DD HH:MM:SS
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_value, fmt)
                    return parsed_date.strftime('%d/%m/%Y %H:%M')
                except ValueError:
                    continue
        
        return str(date_value)
    except Exception:
        return str(date_value)


@register.filter
def add_class(field, css_class):
    """
    Add CSS class to form field
    """
    return field.as_widget(attrs={'class': css_class})


@register.filter
def dict_get(dictionary, key):
    """
    Get value from dictionary by key
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None