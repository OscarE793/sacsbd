# apps/user_management/forms.py
from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile, Role, UserRole
import re

class UserCreateForm(UserCreationForm):
    """Formulario para crear usuarios"""
    
    # Campos del usuario base
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@empresa.com'
        })
    )
    
    # Campos del perfil
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+57 300 123 4567'
        })
    )
    cargo = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Administrador de Base de Datos'
        })
    )
    departamento = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tecnología'
        })
    )
    
    # Configuraciones de acceso
    is_staff = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Acceso al panel de administración'
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Usuario activo'
    )
    
    # Roles
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.filter(activo=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Roles del usuario'
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'nombre.usuario'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar widgets de contraseñas
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Ya existe un usuario con este email.')
        return email
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Validar formato de teléfono
            if not re.match(r'^[\+]?[1-9][\d]{0,15}$', telefono.replace(' ', '')):
                raise ValidationError('Formato de teléfono inválido.')
        return telefono
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_staff = self.cleaned_data.get('is_staff', False)
        user.is_active = self.cleaned_data.get('is_active', True)
        
        if commit:
            user.save()
            
            # Crear o actualizar perfil
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.telefono = self.cleaned_data.get('telefono', '')
            profile.cargo = self.cleaned_data.get('cargo', '')
            profile.departamento = self.cleaned_data.get('departamento', '')
            profile.save()
            
            # Asignar roles
            roles = self.cleaned_data.get('roles', [])
            for role in roles:
                UserRole.objects.get_or_create(
                    user=user,
                    role=role,
                    defaults={'activo': True}
                )
        
        return user


class UserEditForm(forms.ModelForm):
    """Formulario para editar usuarios"""
    
    # Campos del perfil
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+57 300 123 4567'
        })
    )
    cargo = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Administrador de Base de Datos'
        })
    )
    departamento = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tecnología'
        })
    )
    
    # Roles
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.filter(activo=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Roles del usuario'
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'is_staff', 'is_active')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@empresa.com'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Cargar datos del perfil si existe
            try:
                profile = self.instance.profile
                self.fields['telefono'].initial = profile.telefono
                self.fields['cargo'].initial = profile.cargo
                self.fields['departamento'].initial = profile.departamento
            except UserProfile.DoesNotExist:
                pass
            
            # Cargar roles actuales
            current_roles = Role.objects.filter(
                userrole__user=self.instance,
                userrole__activo=True
            )
            self.fields['roles'].initial = current_roles
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe otro usuario con este email.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        
        if commit:
            # Actualizar perfil
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.telefono = self.cleaned_data.get('telefono', '')
            profile.cargo = self.cleaned_data.get('cargo', '')
            profile.departamento = self.cleaned_data.get('departamento', '')
            profile.save()
            
            # Actualizar roles
            # Primero desactivar todos los roles actuales
            UserRole.objects.filter(user=user).update(activo=False)
            
            # Luego activar/crear los roles seleccionados
            roles = self.cleaned_data.get('roles', [])
            for role in roles:
                user_role, created = UserRole.objects.get_or_create(
                    user=user,
                    role=role,
                    defaults={'activo': True}
                )
                if not created:
                    user_role.activo = True
                    user_role.save()
        
        return user


class PasswordChangeForm(forms.Form):
    """Formulario para cambiar contraseña"""
    
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña actual'
        }),
        label='Contraseña actual'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        }),
        label='Nueva contraseña'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        }),
        label='Confirmar nueva contraseña'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError('La contraseña actual es incorrecta.')
        return current_password
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('Las contraseñas no coinciden.')
            
            # Validar fortaleza de la contraseña
            try:
                validate_password(password1, self.user)
            except ValidationError as error:
                raise ValidationError(error)
        
        return password2
    
    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        
        # Actualizar fecha de último cambio de contraseña
        if hasattr(self.user, 'profile'):
            from django.utils import timezone
            self.user.profile.ultimo_cambio_password = timezone.now()
            self.user.profile.cambio_password_requerido = False
            self.user.profile.save()


class RoleForm(forms.ModelForm):
    """Formulario para crear/editar roles"""
    
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Permisos'
    )
    
    class Meta:
        model = Role
        fields = [
            'name', 'description', 'es_administrador', 'puede_gestionar_usuarios',
            'puede_ver_reportes', 'puede_gestionar_backups', 'puede_monitorear_servidores',
            'permissions'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del rol'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del rol'
            }),
            'es_administrador': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'puede_gestionar_usuarios': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'puede_ver_reportes': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'puede_gestionar_backups': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'puede_monitorear_servidores': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Organizar permisos por app
        self.fields['permissions'].queryset = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'name')


class UserFilterForm(forms.Form):
    """Formulario para filtrar usuarios"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, usuario o email...'
        })
    )
    
    role = forms.ModelChoiceField(
        queryset=Role.objects.filter(activo=True),
        required=False,
        empty_label='Todos los roles',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_staff = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('true', 'Staff'),
            ('false', 'No Staff')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
