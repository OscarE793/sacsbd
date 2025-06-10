from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def test_connection(request):
    return JsonResponse({'status': 'ok', 'message': 'Django conectado'})

urlpatterns = [
    
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),    
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('api/', include('monitoring.urls')),  # o el nombre de tu app
    path('api/test/', test_connection),
]
