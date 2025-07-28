# tests/test_authentication.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.authentication.forms import SACSLoginForm

class LoginTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@sacsbd.com',
            password='TestPass123!'
        )
        self.login_url = reverse('authentication:login')
    
    def test_login_page_loads(self):
        """Test que la página de login carga correctamente"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SACS_BD')
        self.assertContains(response, 'Iniciar Sesión')
    
    def test_valid_login(self):
        """Test login con credenciales válidas"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        self.assertRedirects(response, reverse('dashboard:home'))
    
    def test_invalid_login(self):
        """Test login con credenciales inválidas"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña incorrectos')
    
    def test_remember_me_functionality(self):
        """Test funcionalidad Remember Me"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!',
            'remember_me': True,
        })
        self.assertRedirects(response, reverse('dashboard:home'))
        # Verificar que la sesión no expire al cerrar browser
        session = self.client.session
        self.assertNotEqual(session.get_expiry_age(), 0)

class SACSLoginFormTestCase(TestCase):
    def test_form_validation(self):
        """Test validación del formulario"""
        form_data = {
            'username': 'testuser',
            'password': 'TestPass123!',
        }
        form = SACSLoginForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_requires_fields(self):
        """Test que el formulario requiere campos obligatorios"""
        form = SACSLoginForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('password', form.errors)