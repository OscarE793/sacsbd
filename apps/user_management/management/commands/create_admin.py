"""
Comando para crear un superusuario con perfil completo.

Uso:
    python manage.py create_admin --username admin --email admin@example.com
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from apps.user_management.models import UserProfile, Role, UserRole
from apps.user_management.utils import assign_role_to_user
import getpass


class Command(BaseCommand):
    help = 'Crea un superusuario con perfil completo y rol de administrador'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Nombre de usuario',
        )
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email del usuario',
        )
        parser.add_argument(
            '--first-name',
            type=str,
            help='Nombre',
        )
        parser.add_argument(
            '--last-name',
            type=str,
            help='Apellido',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña (si no se proporciona, se solicitará)',
        )
        parser.add_argument(
            '--cargo',
            type=str,
            default='Administrador del Sistema',
            help='Cargo del usuario',
        )
        parser.add_argument(
            '--departamento',
            type=str,
            default='Tecnología',
            help='Departamento del usuario',
        )
        parser.add_argument(
            '--telefono',
            type=str,
            help='Teléfono del usuario',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            raise CommandError(f'El usuario "{username}" ya existe.')
        
        if User.objects.filter(email=email).exists():
            raise CommandError(f'Ya existe un usuario con el email "{email}".')
        
        # Obtener contraseña
        password = options['password']
        if not password:
            password = getpass.getpass('Contraseña: ')
            password_confirm = getpass.getpass('Confirmar contraseña: ')
            
            if password != password_confirm:
                raise CommandError('Las contraseñas no coinciden.')
        
        try:
            with transaction.atomic():
                # Crear usuario
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Actualizar información adicional
                if options['first_name']:
                    user.first_name = options['first_name']
                if options['last_name']:
                    user.last_name = options['last_name']
                user.save()
                
                # Actualizar perfil
                profile = user.profile
                profile.cargo = options['cargo']
                profile.departamento = options['departamento']
                if options['telefono']:
                    profile.telefono = options['telefono']
                profile.save()
                
                # Asignar rol de administrador
                admin_role_assigned = False
                try:
                    admin_role = Role.objects.get(name='Administrador', activo=True)
                    if assign_role_to_user(user, 'Administrador'):
                        admin_role_assigned = True
                        self.stdout.write(
                            self.style.SUCCESS('✓ Rol de Administrador asignado')
                        )
                except Role.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            '⚠ No se encontró el rol de Administrador. '
                            'Ejecuta "python manage.py init_roles" primero.'
                        )
                    )
                
                # Mostrar resumen
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ Superusuario "{username}" creado exitosamente!')
                )
                self.stdout.write('\nDetalles del usuario:')
                self.stdout.write(f'  - Username: {username}')
                self.stdout.write(f'  - Email: {email}')
                self.stdout.write(f'  - Nombre completo: {user.get_full_name() or "No especificado"}')
                self.stdout.write(f'  - Cargo: {profile.cargo}')
                self.stdout.write(f'  - Departamento: {profile.departamento}')
                self.stdout.write(f'  - Es superusuario: Sí')
                self.stdout.write(f'  - Es staff: Sí')
                if admin_role_assigned:
                    self.stdout.write(f'  - Rol asignado: Administrador')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nPuedes iniciar sesión en /admin/ con las credenciales proporcionadas.'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error al crear el usuario: {str(e)}')
            )
            raise