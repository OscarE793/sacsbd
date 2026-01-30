# apps/horas_extras/management/commands/migrar_usuarios_empleados.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.db import transaction
from apps.horas_extras.models import Empleado
from apps.user_management.models import Role, UserRole, UserProfile


class Command(BaseCommand):
    help = 'Migra empleados existentes para vincularlos con usuarios del sistema unificado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la migración sin realizar cambios en la base de datos'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('[MODO SIMULACIÓN - No se guardarán cambios]'))
        else:
            self.stdout.write(self.style.WARNING('[MODO REAL - Se modificará la base de datos]'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[PASO 1] Verificando empleados sin usuario...'))

        empleados_sin_user = Empleado.objects.filter(user__isnull=True)
        self.stdout.write(f'Encontrados: {empleados_sin_user.count()} empleados sin usuario')

        if empleados_sin_user.count() == 0:
            self.stdout.write(self.style.SUCCESS('✓ Todos los empleados tienen usuario asignado'))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('[PASO 2] Creando usuarios para empleados...'))

            usuarios_creados = 0

            for emp in empleados_sin_user:
                username = f"emp_{emp.numero_empleado}"

                # Verificar si el username ya existe
                if User.objects.filter(username=username).exists():
                    username = f"emp_{emp.cedula}"

                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.ERROR(
                        f'✗ El usuario {username} ya existe. Empleado ID: {emp.id}'
                    ))
                    continue

                if not dry_run:
                    try:
                        with transaction.atomic():
                            # Crear usuario
                            user = User.objects.create_user(
                                username=username,
                                first_name=emp.nombres if hasattr(emp, 'nombres') else '',
                                last_name=emp.apellidos if hasattr(emp, 'apellidos') else '',
                                email=emp.email if hasattr(emp, 'email') and emp.email else f"{username}@sacsbd.local",
                                password='TempPassword123!'
                            )

                            # Asegurar que tenga perfil
                            if not hasattr(user, 'profile'):
                                UserProfile.objects.create(
                                    user=user,
                                    telefono=emp.telefono if hasattr(emp, 'telefono') else '',
                                    cargo=emp.get_cargo_display() if hasattr(emp, 'cargo') else '',
                                    cambio_password_requerido=True
                                )

                            # Asignar usuario al empleado
                            emp.user = user
                            emp.save()

                            usuarios_creados += 1
                            self.stdout.write(self.style.SUCCESS(
                                f'✓ Usuario {username} creado para {emp.numero_empleado}'
                            ))

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f'✗ Error creando usuario para {emp.numero_empleado}: {str(e)}'
                        ))
                else:
                    self.stdout.write(
                        f'[SIMULADO] Crearía usuario {username} para empleado {emp.numero_empleado}'
                    )
                    usuarios_creados += 1

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'Usuarios creados: {usuarios_creados}'))

        # Crear/obtener rol de operador
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[PASO 3] Configurando rol de operador de centro de cómputo...'))

        if not dry_run:
            rol_operador, created = Role.objects.get_or_create(
                name='operador de centro de computo',
                defaults={
                    'description': 'Operador de centro de cómputo - Gestión de turnos, monitoreo de servidores y reportes',
                    'puede_ver_reportes': True,
                    'puede_monitorear_servidores': True,
                    'activo': True
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Rol "{rol_operador.name}" creado'))

                # Asignar permisos del módulo horas_extras
                permisos = Permission.objects.filter(content_type__app_label='horas_extras')
                rol_operador.permissions.add(*permisos)
                self.stdout.write(f'✓ {permisos.count()} permisos asignados al rol')
            else:
                self.stdout.write(f'✓ Rol "{rol_operador.name}" ya existe')
        else:
            self.stdout.write('[SIMULADO] Crearía/verificaría rol "operador de centro de computo"')

        # Asignar rol a empleados
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[PASO 4] Asignando rol a empleados...'))

        empleados_activos = Empleado.objects.filter(estado='activo', user__isnull=False)
        self.stdout.write(f'Empleados activos con usuario: {empleados_activos.count()}')

        roles_asignados = 0

        if not dry_run:
            rol_operador = Role.objects.get(name='operador de centro de computo')

            for emp in empleados_activos:
                user_role, created = UserRole.objects.get_or_create(
                    user=emp.user,
                    role=rol_operador,
                    defaults={
                        'activo': True
                    }
                )

                if created:
                    roles_asignados += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Rol asignado a {emp.user.get_full_name() or emp.user.username}'
                    ))
        else:
            roles_asignados = empleados_activos.count()
            self.stdout.write(f'[SIMULADO] Asignaría rol a {roles_asignados} empleados')

        # Resumen final
        self.stdout.write('')
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS('[RESUMEN DE MIGRACIÓN]'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'Total de empleados: {Empleado.objects.count()}')
        self.stdout.write(f'Empleados con usuario: {Empleado.objects.filter(user__isnull=False).count()}')
        self.stdout.write(f'Empleados sin usuario: {Empleado.objects.filter(user__isnull=True).count()}')
        self.stdout.write(f'Roles asignados: {roles_asignados}')

        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('MODO SIMULACIÓN - No se guardaron cambios'))
            self.stdout.write('Ejecuta sin --dry-run para aplicar los cambios:')
            self.stdout.write('  python manage.py migrar_usuarios_empleados')
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('[OK] Migración completada exitosamente!'))
            self.stdout.write('')
            self.stdout.write('Próximos pasos:')
            self.stdout.write('  1. Verifica los usuarios creados en el panel de administración')
            self.stdout.write('  2. Los usuarios creados tienen contraseña temporal: TempPassword123!')
            self.stdout.write('  3. Deberán cambiar su contraseña en el primer login')
            self.stdout.write('  4. Verifica el rol en: http://localhost:8000/usuarios/roles/')
