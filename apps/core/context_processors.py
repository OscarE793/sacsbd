"""
Procesadores de contexto personalizados para SACSBD
"""

def sacsbd_context(request):
    """
    Agrega variables de contexto globales para SACSBD
    """
    return {
        'app_name': 'SACSBD',
        'app_version': '1.0.0',
        'theme_name': 'Heon',
        'company_name': 'SACSBD System',
        'current_year': 2025,
    }
