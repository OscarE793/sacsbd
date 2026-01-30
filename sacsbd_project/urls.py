# sacsbd_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_dashboard(request):
    """Redireccionar la página principal al dashboard"""
    if request.user.is_authenticated:
        return redirect('reportes:dashboard')
    else:
        return redirect('authentication:login')

urlpatterns = [
    # Página principal
    path('', redirect_to_dashboard, name='home'),

    # Apps principales
    path('auth/', include('authentication.urls', namespace='authentication')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
    path('users/', include('apps.user_management.urls', namespace='user_management')),
    path('recargos/', include('apps.horas_extras.urls', namespace='horas_extras')),

    # Admin de Django
    path('admin/', admin.site.urls),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Servir desde directorios de desarrollo (STATICFILES_DIRS)
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
