from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
from django.db import transaction
import json
from datetime import datetime, timedelta

from .models import RegistroTurno, TipoTurno, PatronOperador
from apps.user_management.models import Role

def es_administrador(user):
    return user.is_superuser or user.is_staff or user.userrole_set.filter(role__name__in=['admin', 'supervisor']).exists()

@login_required
@user_passes_test(es_administrador)
def calendario_asignacion(request):
    """
    Vista principal del calendario de asignación de turnos.
    Permite visualizar y asignar turnos explícitamente a los operadores.
    """
    # Obtener todos los operadores activos
    # Nota: Ajustar el filtro de rol según la configuración exacta de tu proyecto
    # Usamos userrole__role__name porque la relación es a través de UserRole y el campo es 'name'
    operadores = User.objects.filter(
        is_active=True,
        userrole__role__name='operador de centro de computo'
    ).order_by('first_name', 'last_name').distinct()
    
    tipos_turno = TipoTurno.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'operadores': operadores,
        'tipos_turno': tipos_turno,
        'page_title': 'Asignación de Turnos',
        'current_date': datetime.now().date(),
    }
    return render(request, 'horas_extras/asignacion/calendario.html', context)

@login_required
@user_passes_test(es_administrador)
def obtener_eventos_calendario(request):
    """
    API para obtener los eventos (turnos) para el calendario.
    Recibe start y end (fechas) y opcionalmente update_id (operador).
    """
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    operador_id = request.GET.get('operador_id') # Si se filtra por un solo operador
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'Fechas requeridas'}, status=400)
    
    # Parsear fechas (FullCalendar envía ISO8601)
    start = parse_date(start_date.split('T')[0])
    end = parse_date(end_date.split('T')[0])
    
    query = RegistroTurno.objects.filter(fecha__range=[start, end])
    
    if operador_id:
        query = query.filter(operador_id=operador_id)
    else:
        # Si son muchos eventos, puede ser pesado.
        # Aquí filtramos solo operadores activos para no traer basura histórica si no es necesaria
        query = query.filter(operador__is_active=True)
    
    # Importar calculadora para obtener horas y festivos
    from .calculos_legales import CalculadoraLegal
    calculadora = CalculadoraLegal()
        
    eventos = []
    colores_turno = {
        'manana': '#ffc107', # Amarillo (Warning) - Turno M
        'tarde': '#fd7e14',  # Naranja - Turno T
        'noche': '#6610f2',  # Morado (Indigo) - Turno N
        'descanso': '#20c997', # Verde agua (Teal) - Descanso
        'apoyo': '#0d6efd',  # Azul (Primary) - Apoyo
    }
    
    for turno in query:
        # Determinar color basado en coincidencias parciales si no es exacto
        codigo_lower = turno.tipo_turno.codigo.lower()
        nombre_lower = turno.tipo_turno.nombre.lower()
        
        color = '#6c757d' # Gris (Secondary) por defecto
        
        if 'apoyo' in nombre_lower or 'apoyo' in codigo_lower:
            color = colores_turno['apoyo']
        elif 'manana' in nombre_lower or 'mañana' in nombre_lower or 'm' in codigo_lower:
             # Ajuste: si es M puro usa amarillo, si T puro usa naranja
             if 'm' in codigo_lower and 't' not in codigo_lower: 
                 color = colores_turno['manana']
             else:
                 color = colores_turno['manana'] # Fallback
        
        # Override para especificos comunes sacados de la imagen
        if 't' in codigo_lower and 'm' not in codigo_lower:
            color = colores_turno['tarde']
            
        if turno.tipo_turno.es_nocturno or 'n' in codigo_lower:
            color = colores_turno['noche']
            
        if 'descanso' in nombre_lower or 'd' in codigo_lower:
            color = colores_turno['descanso']
        
        # Calcular horas para el tooltip
        resultado_horas = calculadora.calcular_horas_turno(turno)
        horas_del_dia = resultado_horas.get(turno.fecha, {
            'HOD': 0, 'RNO': 0, 'RDF': 0, 'RNF': 0, 'TOTAL': 0
        })
        
        # Verificar si es festivo
        es_festivo = calculadora.es_festivo(turno.fecha) or turno.fecha.weekday() == 6
            
        eventos.append({
            'id': turno.id,
            'resourceId': turno.operador_id, # Para vista de recursos si se usa
            'title': f"{turno.tipo_turno.codigo}",
            'start': turno.fecha.isoformat(),
            'allDay': True,
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'tipo_turno_id': turno.tipo_turno_id,
                'operador_nombre': turno.operador.get_full_name(),
                'codigo_turno': turno.tipo_turno.codigo,
                'es_festivo': es_festivo,
                'horas': {
                    'HOD': float(horas_del_dia.get('HOD', 0)),
                    'RNO': float(horas_del_dia.get('RNO', 0)),
                    'RDF': float(horas_del_dia.get('RDF', 0)),
                    'RNF': float(horas_del_dia.get('RNF', 0)),
                    'TOTAL': float(horas_del_dia.get('TOTAL', 0))
                }
            }
        })
        
    return JsonResponse(eventos, safe=False)

@login_required
@user_passes_test(es_administrador)
@require_POST
def asignar_turno_api(request):
    """
    API para crear o actualizar un turno explícito.
    Recibe JSON: {
        "operador_id": 1,
        "fecha": "2026-01-27",
        "tipo_turno_id": 5
    }
    """
    try:
        data = json.loads(request.body)
        operador_id = data.get('operador_id')
        fecha_str = data.get('fecha')
        tipo_turno_id = data.get('tipo_turno_id')
        
        if not all([operador_id, fecha_str, tipo_turno_id]):
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
            
        fecha = parse_date(fecha_str)
        if not fecha:
            return JsonResponse({'error': 'Fecha inválida'}, status=400)
            
        operador = get_object_or_404(User, pk=operador_id)
        tipo_turno = get_object_or_404(TipoTurno, pk=tipo_turno_id)
        
        # --- CÁLCULO DE HORAS REALES (FIX: HOD 7h Bug) ---
        from .utils import GeneradorTurnosV4
        
        # Determinar contexto para turno N (Vecindad)
        context_vecindad = None
        if tipo_turno.codigo == 'N':
            cutoff = datetime.combine(fecha, datetime.min.time())
            # Buscar turno ayer y mañana para validar vecindad
            prev_reg = RegistroTurno.objects.filter(operador=operador, fecha=fecha - timedelta(days=1)).first()
            next_reg = RegistroTurno.objects.filter(operador=operador, fecha=fecha + timedelta(days=1)).first()
            
            context_vecindad = {
                'prev': prev_reg.tipo_turno.codigo if prev_reg else None,
                'today': 'N',
                'next': next_reg.tipo_turno.codigo if next_reg else None
            }
            
        ranges = GeneradorTurnosV4.obtener_rangos_horarios(tipo_turno.codigo, fecha, context_vecindad)
        
        hora_inicio_real = None
        hora_fin_real = None
        
        if ranges:
            # Asumimos bloque continuo o tomamos extremos (para N v5 funciona bien)
            hora_inicio_real = ranges[0]['inicio']
            hora_fin_real = ranges[-1]['fin']
            
        # Operación atómica para evitar duplicados raciales
        with transaction.atomic():
            registro, created = RegistroTurno.objects.update_or_create(
                operador=operador,
                fecha=fecha,
                defaults={
                    'tipo_turno': tipo_turno,
                    'estado': 'programado',
                    'hora_inicio_real': hora_inicio_real,
                    'hora_fin_real': hora_fin_real,
                    # Resetear horas calculadas:
                    # 'horas_programadas': calculada por signals o save()
                }
            )
            # Forzar el save para disparar la logica de horas_programadas en models.py
            registro.save()
            
        return JsonResponse({
            'success': True, 
            'message': 'Turno asignado correctamente',
            'registro_id': registro.id,
            'accion': 'creado' if created else 'actualizado'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
