"""
Comando para inicializar los roles por defecto del sistema.

Uso:
    python manage.py init_roles
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.user_management.models import Role
from apps.user_management.utils import create_default_roles


class Command(BaseCommand):
    help = 'Inicializa los roles por defecto del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recreación de roles aunque ya existan',
        )

    def handle(self, *args, **options):
        self.stdout.write('Inicializando roles del sistema...')
        
        try:
            with transaction.atomic():
                if options['force']:
                    # Si se fuerza, primero desactivar todos los roles existentes
                    Role.objects.all().update(activo=False)
                    self.stdout.write(
                        self.style.WARNING('Todos los roles existentes han sido desactivados.')
                    )
                
                # Crear roles por defecto
                if create_default_roles():
                    self.stdout.write(
                        self.style.SUCCESS('✓ Roles creados exitosamente')
                    )
                    
                    # Mostrar resumen
                    roles = Role.objects.filter(activo=True)
                    self.stdout.write('\nRoles activos en el sistema:')
                    for role in roles:
                        permisos = []
                        if role.es_administrador:
                            permisos.append('Administrador')
                        if role.puede_gestionar_usuarios:
                            permisos.append('Gestión de Usuarios')
                        if role.puede_ver_reportes:
                            permisos.append('Ver Reportes')
                        if role.puede_gestionar_backups:
                            permisos.append('Gestión de Backups')
                        if role.puede_monitorear_servidores:
                            permisos.append('Monitoreo de Servidores')
                        
                        permisos_str = ', '.join(permisos) if permisos else 'Sin permisos especiales'
                        self.stdout.write(f'  - {role.name}: {permisos_str}')
                else:
                    self.stdout.write(
                        self.style.ERROR('✗ Error al crear los roles')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error: {str(e)}')
            )
            raise