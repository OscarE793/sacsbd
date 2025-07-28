# apps/authentication/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import PasswordResetView
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

@csrf_protect
@never_cache
def login_view(request):
    """Vista de login con diseño Metronic/SACSBD"""
    
    if request.user.is_authenticated:
        return redirect('reportes:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Configurar sesión según "Remember Me"
                    if not remember_me:
                        request.session.set_expiry(0)  # Expira al cerrar browser
                    else:
                        request.session.set_expiry(1209600)  # 2 semanas
                    
                    # Mensaje de bienvenida
                    messages.success(request, f'¡Bienvenido {user.get_full_name() or user.username}!')
                    
                    # Redirect to next or dashboard
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('reportes:dashboard')
                else:
                    messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
            else:
                messages.error(request, 'Credenciales inválidas. Verifica tu usuario y contraseña.')
        else:
            messages.error(request, 'Por favor ingresa usuario y contraseña.')
    
    return render(request, 'auth/login.html')

@login_required
def logout_view(request):
    """Vista de logout"""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'Sesión cerrada exitosamente. ¡Hasta pronto, {user_name}!')
    return redirect('authentication:login')

def register_view(request):
    """Vista de registro (placeholder)"""
    return render(request, 'auth/register.html')

def forgot_password_view(request):
    """Vista de recuperación de contraseña"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Aquí implementar lógica de recuperación
            messages.success(request, 'Si el email existe, recibirás instrucciones para recuperar tu contraseña.')
            return redirect('authentication:login')
        else:
            messages.error(request, 'Por favor ingresa un email válido.')
    
    return render(request, 'auth/forgot_password.html')

class SACSPasswordResetView(PasswordResetView):
    """Vista personalizada para reseteo de contraseña"""
    template_name = 'auth/forgot_password.html'
    email_template_name = 'auth/password_reset_email.html'
    success_url = reverse_lazy('authentication:password_reset_done')
    
    def form_valid(self, form):
        messages.success(self.request, 'Si el email existe en nuestro sistema, recibirás instrucciones para restablecer tu contraseña.')
        return super().form_valid(form)
