from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

# Create your tests here.

class ReportesViewsTest(TestCase):
    """Tests para las vistas de reportes"""
    
    def setUp(self):
        """Configurar usuario de prueba"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_dashboard_requires_login(self):
        """Verificar que el dashboard requiere login"""
        response = self.client.get(reverse('reportes:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirección a login
    
    def test_dashboard_with_login(self):
        """Verificar acceso al dashboard con login"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('reportes:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    # Agregar más tests según sea necesario
