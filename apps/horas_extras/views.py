# apps/horas_extras/views.py - VERSIÓN SIMPLIFICADA
# Sistema SOLO calcula horas, no valores monetarios
# Operadores identificados por rol "operador de centro de computo" en user_management

from .exportador import ExportadorReportes
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, date, timedelta
import json
import calendar
from decimal import Decimal

from .models import TipoTurno, DiaFestivo, RegistroTurno, ResumenMensual
from apps.user_management.models import Role, UserRole

from .utils import (
    CalculadoraHorasExtras, GeneradorTurnos, ReportesHorasExtras,
    ValidadorTurnos
)
from .calculos_legales import CalculadoraLegal
from .forms import RegistroTurnoForm, FiltroReporteForm, GenerarTurnosForm


def obtener_operadores_activos():
    """Obtiene todos los usuarios con rol de operador de centro de cómputo activos"""
    try:
        rol_operador = Role.objects.get(name='operador de centro de computo')
        return User.objects.filter(
            is_active=True,
            userrole__role=rol_operador,
            userrole__activo=True
        ).select_related('profile').distinct().order_by('last_name', 'first_name')
    except Role.DoesNotExist:
        return User.objects.none()


@login_required
def dashboard_horas_extras(request):
    """Vista principal del dashboard de horas extras"""

    # Obtener mes y año actuales
    hoy = date.today()
    mes_actual = request.GET.get('mes', hoy.month)
    ano_actual = request.GET.get('ano', hoy.year)

    try:
        mes_actual = int(mes_actual)
        ano_actual = int(ano_actual)
    except (ValueError, TypeError):
        mes_actual = hoy.month
        ano_actual = hoy.year

    # Estadísticas del mes actual
    operadores = obtener_operadores_activos()
    turnos_mes = RegistroTurno.objects.filter(
        fecha__year=ano_actual,
        fecha__month=mes_actual
    )

    stats = {
        'total_operadores': operadores.count(),
        'total_turnos_mes': turnos_mes.count(),
        'turnos_trabajados': turnos_mes.filter(estado='trabajado').count(),
        'turnos_pendientes': turnos_mes.filter(estado='programado').count(),
        'horas_trabajadas_mes': turnos_mes.filter(estado='trabajado').aggregate(
            total=Sum('horas_trabajadas')
        )['total'] or Decimal('0.00'),
        'dias_festivos_mes': DiaFestivo.objects.filter(
            fecha__year=ano_actual,
            fecha__month=mes_actual,
            activo=True
        ).count()
    }

    # Operadores con más horas este mes
    operadores_top = turnos_mes.filter(
        estado='trabajado'
    ).values(
        'operador__first_name', 'operador__last_name', 'operador__username'
    ).annotate(
        total_horas=Sum('horas_trabajadas'),
        total_turnos=Count('id')
    ).order_by('-total_horas')[:5]

    # Calendario del mes con festivos
    calendario = CalculadoraHorasExtras.generar_calendario_mes(ano_actual, mes_actual)

    # Próximos días festivos
    proximos_festivos = DiaFestivo.objects.filter(
        fecha__gte=hoy,
        activo=True
    ).order_by('fecha')[:5]

    context = {
        'stats': stats,
        'operadores_top': operadores_top,
        'calendario': calendario,
        'proximos_festivos': proximos_festivos,
        'mes_actual': mes_actual,
        'ano_actual': ano_actual,
        'nombre_mes': calendar.month_name[mes_actual],
        'meses': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'anos': list(range(2024, 2030))
    }

    return render(request, 'horas_extras/dashboard.html', context)


@login_required
def lista_operadores(request):
    """Vista para listar operadores del sistema"""

    busqueda = request.GET.get('q', '')

    operadores = obtener_operadores_activos()

    if busqueda:
        operadores = operadores.filter(
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(username__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )

    # Paginación
    paginator = Paginator(operadores, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
    }

    return render(request, 'horas_extras/operadores/lista.html', context)


@login_required
def detalle_operador(request, operador_id):
    """Vista de detalle de un operador"""

    operador = get_object_or_404(User, id=operador_id)

    # Verificar que es operador
    if not obtener_operadores_activos().filter(id=operador_id).exists():
        messages.error(request, 'El usuario no es un operador de centro de cómputo')
        return redirect('horas_extras:dashboard')

    # Obtener mes y año para filtros
    hoy = date.today()
    mes = request.GET.get('mes', hoy.month)
    ano = request.GET.get('ano', hoy.year)

    try:
        mes = int(mes)
        ano = int(ano)
    except (ValueError, TypeError):
        mes = hoy.month
        ano = hoy.year

    # Turnos del mes
    turnos = RegistroTurno.objects.filter(
        operador=operador,
        fecha__year=ano,
        fecha__month=mes
    ).order_by('fecha').select_related('tipo_turno')

    # Generar reporte del mes
    reporte = ReportesHorasExtras.reporte_operador_mes(operador, ano, mes)

    # Resumen mensual si existe
    try:
        resumen_mensual = ResumenMensual.objects.get(
            operador=operador,
            mes=mes,
            ano=ano
        )
    except ResumenMensual.DoesNotExist:
        resumen_mensual = None

    context = {
        'operador': operador,
        'turnos': turnos,
        'reporte': reporte,
        'resumen_mensual': resumen_mensual,
        'mes': mes,
        'ano': ano,
        'nombre_mes': calendar.month_name[mes],
        'meses': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'anos': list(range(2024, 2030))
    }

    return render(request, 'horas_extras/operadores/detalle.html', context)


@login_required
def calendario_turnos(request):
    """Vista del calendario de turnos"""

    # Obtener mes y año
    hoy = date.today()
    mes = request.GET.get('mes', hoy.month)
    ano = request.GET.get('ano', hoy.year)
    operador_id = request.GET.get('operador')

    try:
        mes = int(mes)
        ano = int(ano)
    except (ValueError, TypeError):
        mes = hoy.month
        ano = hoy.year

    # Obtener operadores desde el sistema de roles
    operadores = obtener_operadores_activos()
    tipos_turno = TipoTurno.objects.filter(activo=True).order_by('nombre')
    operador_seleccionado = None

    if operador_id:
        try:
            operador_seleccionado = operadores.get(id=operador_id)
        except User.DoesNotExist:
            pass

    context = {
        'operadores': operadores,
        'tipos_turno': tipos_turno,
        'operador_seleccionado': operador_seleccionado,
        'mes': mes,
        'ano': ano,
        'nombre_mes': calendar.month_name[mes],
        'meses': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'anos': list(range(2024, 2030))
    }

    return render(request, 'horas_extras/calendario/calendario.html', context)


@login_required
def registrar_turno(request):
    """Vista para registrar un nuevo turno"""

    if request.method == 'POST':
        form = RegistroTurnoForm(request.POST)
        if form.is_valid():
            turno = form.save()

            # Validar el turno
            errores = ValidadorTurnos.validar_turno(turno)
            if errores:
                for error in errores:
                    messages.error(request, error)
                turno.delete()
            else:
                messages.success(request, 'Turno registrado exitosamente')
                return redirect('horas_extras:detalle_operador', operador_id=turno.operador.id)
    else:
        # Pre-llenar con operador y fecha si se proporcionan
        operador_id = request.GET.get('operador')
        fecha = request.GET.get('fecha')

        initial = {}
        if operador_id:
            try:
                operador = User.objects.get(id=operador_id)
                initial['operador'] = operador
            except User.DoesNotExist:
                pass

        if fecha:
            try:
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
                initial['fecha'] = fecha_obj
            except ValueError:
                pass

        form = RegistroTurnoForm(initial=initial)

    context = {
        'form': form,
        'title': 'Registrar Nuevo Turno'
    }

    return render(request, 'horas_extras/turnos/form.html', context)


@login_required
def editar_turno(request, turno_id):
    """Vista para editar un turno existente"""

    turno = get_object_or_404(RegistroTurno, id=turno_id)

    if request.method == 'POST':
        form = RegistroTurnoForm(request.POST, instance=turno)
        if form.is_valid():
            turno_actualizado = form.save()

            # Validar el turno
            errores = ValidadorTurnos.validar_turno(turno_actualizado)
            if errores:
                for error in errores:
                    messages.error(request, error)
            else:
                messages.success(request, 'Turno actualizado exitosamente')
                return redirect('horas_extras:detalle_operador', operador_id=turno.operador.id)
    else:
        form = RegistroTurnoForm(instance=turno)

    context = {
        'form': form,
        'turno': turno,
        'title': f'Editar Turno - {turno.operador.get_full_name()} ({turno.fecha})'
    }

    return render(request, 'horas_extras/turnos/form.html', context)


@login_required
def generar_turnos_automaticos(request):
    """Vista para generar turnos automáticos"""

    if request.method == 'POST':
        form = GenerarTurnosForm(request.POST)
        if form.is_valid():
            operador_id = form.cleaned_data['operador_id']
            mes = int(form.cleaned_data['mes'])
            ano = int(form.cleaned_data['ano'])
            patron_inicial = form.cleaned_data['patron_inicial']
            sobrescribir = form.cleaned_data['sobrescribir']

            try:
                operador = User.objects.get(id=operador_id)

                # Verificar si ya existen turnos
                turnos_existentes = RegistroTurno.objects.filter(
                    operador=operador,
                    fecha__year=ano,
                    fecha__month=mes
                ).count()

                if turnos_existentes > 0 and not sobrescribir:
                    messages.warning(
                        request,
                        f'Ya existen {turnos_existentes} turnos para {operador.get_full_name()} en {calendar.month_name[mes]} {ano}. '
                        'Marque "Sobrescribir existentes" para reemplazarlos.'
                    )
                else:
                    # Eliminar turnos existentes si se va a sobrescribir
                    if sobrescribir:
                        RegistroTurno.objects.filter(
                            operador=operador,
                            fecha__year=ano,
                            fecha__month=mes
                        ).delete()

                    # Generar nuevos turnos
                    turnos_nuevos = GeneradorTurnos.generar_turnos_mes(
                        operador, ano, mes, patron_inicial
                    )

                    # Guardar turnos
                    turnos_guardados = GeneradorTurnos.guardar_turnos_mes(turnos_nuevos)

                    messages.success(
                        request,
                        f'Se generaron {len(turnos_guardados)} turnos para {operador.get_full_name()} '
                        f'en {calendar.month_name[mes]} {ano}'
                    )

                    return redirect('horas_extras:detalle_operador', operador_id=operador.id)

            except Exception as e:
                messages.error(request, f'Error al generar turnos: {str(e)}')
    else:
        # Pre-llenar con operador si se proporciona
        operador_id = request.GET.get('operador')

        # Mes y año actuales
        hoy = date.today()
        initial = {
            'mes': str(hoy.month),
            'ano': str(hoy.year)
        }

        if operador_id:
            initial['operador_id'] = operador_id

        form = GenerarTurnosForm(initial=initial)

    # Agregar lista de operadores al contexto
    operadores = obtener_operadores_activos()

    context = {
        'form': form,
        'operadores': operadores,
        'title': 'Generar Turnos Automáticos'
    }

    return render(request, 'horas_extras/turnos/generar.html', context)


@login_required
def reportes_horas_extras(request):
    """
    Vista unificada para generar reportes de horas extras y recargos.
    Permite filtrar y ver resultados en la misma página.
    """
    context = {
        'title': 'Reportes de Horas Trabajadas',
        'datos': None,
        'totales_generales': None
    }

    # Procesar formulario (GET para permitir URLs compartibles, o POST si se prefiere)
    # Usamos GET para que el usuario pueda refrescar o guardar la URL del reporte
    if request.GET:
        form = FiltroReporteForm(request.GET)
        if form.is_valid():
            mes = int(form.cleaned_data['mes'])
            ano = int(form.cleaned_data['ano'])
            tipo_reporte = form.cleaned_data['tipo_reporte']
            operador_id = form.cleaned_data.get('operador_id')

            # Determinar operadores a procesar
            if tipo_reporte == 'individual' and operador_id:
                operadores = User.objects.filter(id=operador_id)
            else:
                operadores = obtener_operadores_activos()
            
            # Rangos de fecha
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            fecha_inicio = date(ano, mes, 1)
            fecha_fin = date(ano, mes, ultimo_dia)
            
            # Para turnos nocturnos que cruzan medianoche, necesitamos incluir
            # el último día del mes anterior (su turno puede terminar en este mes)
            if mes == 1:
                fecha_busqueda_inicio = date(ano - 1, 12, 31)
            else:
                ultimo_dia_mes_anterior = calendar.monthrange(ano, mes - 1)[1]
                fecha_busqueda_inicio = date(ano, mes - 1, ultimo_dia_mes_anterior)
            
            # Obtener turnos (incluyendo día anterior para continuidad de turno N)
            turnos = RegistroTurno.objects.filter(
                fecha__range=(fecha_busqueda_inicio, fecha_fin),
                operador__in=operadores
            ).select_related('tipo_turno', 'operador')

            
            # Mapeo optimizado
            turnos_map = {}
            for t in turnos:
                if t.operador_id not in turnos_map:
                    turnos_map[t.operador_id] = {}
                turnos_map[t.operador_id][t.fecha] = t
            
            # Calcular
            calculadora = CalculadoraLegal()
            datos_reporte = []
            
            # Acumuladores globales
            gran_totales = {
                'HOD': Decimal(0), 'RNO': Decimal(0),
                'RDF': Decimal(0), 'RNF': Decimal(0),
                'TOTAL': Decimal(0)
            }
            
            for operador in operadores:
                # Inicializar acumulador diario para el operador
                acumulado_diario = {}
                for d in range(1, ultimo_dia + 1):
                    f = date(ano, mes, d)
                    acumulado_diario[f] = {
                        'HOD': Decimal(0), 'RNO': Decimal(0), 
                        'RDF': Decimal(0), 'RNF': Decimal(0), 
                        'TOTAL': Decimal(0)
                    }
                
                # Calcular horas reales de todos los turnos
                turnos_op = [t for t in turnos if t.operador_id == operador.id]
                for turno in turnos_op:
                    if turno.tipo_turno:
                        # Siempre usar calcular_horas_turno (usa horas del TipoTurno por día)
                        resultado = calculadora.calcular_horas_turno(turno)
                        
                        # Agregar al acumulado diario
                        for fecha_res, horas_res in resultado.items():
                            if fecha_inicio <= fecha_res <= fecha_fin:
                                for k in ['HOD', 'RNO', 'RDF', 'RNF', 'TOTAL']:
                                    acumulado_diario[fecha_res][k] += horas_res.get(k, Decimal(0))
                
                # Construir estructura para el reporte
                info_operador = {
                    'nombre': operador.get_full_name() or operador.username,
                    'id': operador.id,
                    'dias': [],
                    'totales': {
                        'HOD': Decimal(0), 'RNO': Decimal(0), 
                        'RDF': Decimal(0), 'RNF': Decimal(0), 
                        'TOTAL': Decimal(0)
                    }
                }
                
                for dia in range(1, ultimo_dia + 1):
                    fecha_iter = date(ano, mes, dia)
                    turno_visual = turnos_map.get(operador.id, {}).get(fecha_iter)
                    
                    detalle_dia = {
                        'fecha': fecha_iter,
                        'dia_semana': fecha_iter.strftime('%A'),
                        'turno': turno_visual.tipo_turno.codigo if (turno_visual and turno_visual.tipo_turno) else 'Descanso',
                        'es_festivo': calculadora.es_festivo(fecha_iter) or fecha_iter.weekday() == 6,
                        'horas': acumulado_diario.get(fecha_iter)
                    }
                    
                    info_operador['dias'].append(detalle_dia)
                    
                    # Sumar a totales del operador
                    for k in info_operador['totales']:
                        info_operador['totales'][k] += detalle_dia['horas'][k]
                
                datos_reporte.append(info_operador)
                
                # Sumar a totales globales
                for k in gran_totales:
                    gran_totales[k] += info_operador['totales'][k]
            
            context['datos'] = datos_reporte
            context['totales_generales'] = gran_totales
            context['porcentajes'] = {
                'RNO': '35%',
                'RDF': '75%',
                'RNF': '110%'
            }

    else:
        hoy = date.today()
        form = FiltroReporteForm(initial={
            'mes': str(hoy.month),
            'ano': str(hoy.year),
            'tipo_reporte': 'todos'
        })
    
    context['form'] = form
    return render(request, 'horas_extras/reporte_unificado.html', context)


@login_required
def ajax_horarios_turno(request):
    """Vista AJAX para obtener horarios de un turno según la fecha"""

    tipo_turno_id = request.GET.get('tipo_turno_id')
    fecha_str = request.GET.get('fecha')

    if not tipo_turno_id or not fecha_str:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        tipo_turno = TipoTurno.objects.get(id=tipo_turno_id)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        hora_inicio, hora_fin, horas = tipo_turno.get_horario_por_dia(fecha)

        response_data = {
            'hora_inicio': hora_inicio.strftime('%H:%M') if hora_inicio else None,
            'hora_fin': hora_fin.strftime('%H:%M') if hora_fin else None,
            'horas_programadas': str(horas),
            'es_nocturno': tipo_turno.es_nocturno,
            'dia_semana': fecha.weekday(),
            'nombre_dia': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][fecha.weekday()]
        }

        return JsonResponse(response_data)

    except (TipoTurno.DoesNotExist, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def ajax_calendario_data(request):
    """Vista AJAX para obtener datos del calendario con horas calculadas"""

    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    operador_id = request.GET.get('operador_id')

    if not mes or not ano:
        return JsonResponse({'error': 'Mes y año son requeridos'}, status=400)

    try:
        mes = int(mes)
        ano = int(ano)

        # Generar calendario
        calendario = CalculadoraHorasExtras.generar_calendario_mes(ano, mes)
        
        # Rango de fechas
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        fecha_inicio = date(ano, mes, 1)
        fecha_fin = date(ano, mes, ultimo_dia)
        
        # Para continuidad de turno N, incluir día anterior
        if mes == 1:
            fecha_busqueda = date(ano - 1, 12, 31)
        else:
            ultimo_dia_ant = calendar.monthrange(ano, mes - 1)[1]
            fecha_busqueda = date(ano, mes - 1, ultimo_dia_ant)

        # Obtener operadores activos
        if operador_id:
            operadores = obtener_operadores_activos().filter(id=operador_id)
        else:
            operadores = obtener_operadores_activos()

        # Obtener todos los turnos (incluyendo día anterior para continuidad)
        turnos_query = RegistroTurno.objects.filter(
            fecha__range=(fecha_busqueda, fecha_fin)
        ).select_related('operador', 'tipo_turno')

        # Calculadora
        calculadora = CalculadoraLegal()
        
        # Pre-calcular horas para todos los turnos y agregar por día
        horas_calculadas = {}  # {operador_id: {fecha_str: {HOD, RNO, RDF, RNF, TOTAL}}}
        turnos_visual = {}  # {operador_id: {fecha_str: turno_info}}
        
        for turno in turnos_query:
            op_id = turno.operador.id
            fecha_str = turno.fecha.strftime('%Y-%m-%d')
            
            # Guardar turno visual (el que inicia ese día)
            if op_id not in turnos_visual:
                turnos_visual[op_id] = {}
            if turno.fecha >= fecha_inicio:  # Solo mostrar turnos del mes actual
                turnos_visual[op_id][fecha_str] = {
                    'id': turno.id,
                    'tipo_turno': turno.tipo_turno.codigo if turno.tipo_turno else 'D',
                    'estado': turno.estado,
                }
            
            # Calcular horas reales
            if turno.tipo_turno:
                resultado = calculadora.calcular_horas_turno(turno)
                
                # Agregar al acumulador por fecha
                if op_id not in horas_calculadas:
                    horas_calculadas[op_id] = {}
                    
                for fecha_calc, horas in resultado.items():
                    if fecha_inicio <= fecha_calc <= fecha_fin:
                        fecha_calc_str = fecha_calc.strftime('%Y-%m-%d')
                        if fecha_calc_str not in horas_calculadas[op_id]:
                            horas_calculadas[op_id][fecha_calc_str] = {
                                'HOD': Decimal(0), 'RNO': Decimal(0),
                                'RDF': Decimal(0), 'RNF': Decimal(0),
                                'TOTAL': Decimal(0)
                            }
                        for k in ['HOD', 'RNO', 'RDF', 'RNF', 'TOTAL']:
                            horas_calculadas[op_id][fecha_calc_str][k] += horas.get(k, Decimal(0))

        # Preparar respuesta con operadores
        operadores_data = []
        for operador in operadores:
            turnos_operador = {}
            
            for dia in calendario:
                fecha_str = dia['fecha'].strftime('%Y-%m-%d')
                turno_info = turnos_visual.get(operador.id, {}).get(fecha_str)
                horas_info = horas_calculadas.get(operador.id, {}).get(fecha_str, {
                    'HOD': Decimal(0), 'RNO': Decimal(0),
                    'RDF': Decimal(0), 'RNF': Decimal(0),
                    'TOTAL': Decimal(0)
                })
                
                if turno_info:
                    turnos_operador[fecha_str] = {
                        'id': turno_info['id'],
                        'tipo_turno': turno_info['tipo_turno'],
                        'estado': turno_info['estado'],
                        'HOD': str(horas_info['HOD']),
                        'RNO': str(horas_info['RNO']),
                        'RDF': str(horas_info['RDF']),
                        'RNF': str(horas_info['RNF']),
                        'TOTAL': str(horas_info['TOTAL']),
                    }
                else:
                    turnos_operador[fecha_str] = None

            operadores_data.append({
                'id': operador.id,
                'nombre': operador.get_full_name() or operador.username,
                'username': operador.username,
                'email': operador.email,
                'turnos': turnos_operador
            })

        # Preparar datos del calendario
        calendar_data = []
        for dia in calendario:
            fecha_str = dia['fecha'].strftime('%Y-%m-%d')
            calendar_data.append({
                'fecha': fecha_str,
                'dia': dia['dia'],
                'dia_semana': dia['dia_semana'],
                'nombre_dia': dia['nombre_dia'],
                'es_festivo': dia['es_festivo'],
                'es_domingo': dia['es_domingo'],
                'es_sabado': dia['es_sabado'],
                'festivo_info': dia['festivo_info']
            })

        return JsonResponse({
            'calendario': calendar_data,
            'operadores': operadores_data,
            'mes': mes,
            'ano': ano,
            'nombre_mes': calendar.month_name[mes]
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def ajax_asignar_turnos(request):
    """Vista AJAX para asignar turnos a un operador en múltiples días"""

    try:
        data = json.loads(request.body)
        operador_id = data.get('operador_id')
        fechas = data.get('fechas', [])
        tipo_turno_id = data.get('tipo_turno_id')
        sobrescribir = data.get('sobrescribir', False)

        if not operador_id or not fechas or not tipo_turno_id:
            return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)

        operador = User.objects.get(id=operador_id)
        tipo_turno = TipoTurno.objects.get(id=tipo_turno_id)

        turnos_creados = 0
        turnos_actualizados = 0
        turnos_existentes = 0
        errores = []

        for fecha_str in fechas:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

                # Verificar si ya existe un turno
                turno_existente = RegistroTurno.objects.filter(
                    operador=operador,
                    fecha=fecha
                ).first()

                if turno_existente and not sobrescribir:
                    turnos_existentes += 1
                    continue

                # Obtener horarios del turno según el día de la semana
                hora_inicio, hora_fin, horas = tipo_turno.get_horario_por_dia(fecha)

                if turno_existente and sobrescribir:
                    # Actualizar turno existente
                    turno_existente.tipo_turno = tipo_turno
                    turno_existente.hora_inicio_real = hora_inicio
                    turno_existente.hora_fin_real = hora_fin
                    turno_existente.horas_programadas = horas
                    turno_existente.estado = 'programado'
                    turno_existente.save()
                    turnos_actualizados += 1
                else:
                    # Crear nuevo turno
                    RegistroTurno.objects.create(
                        operador=operador,
                        tipo_turno=tipo_turno,
                        fecha=fecha,
                        hora_inicio_real=hora_inicio,
                        hora_fin_real=hora_fin,
                        horas_programadas=horas,
                        horas_trabajadas=Decimal('0.00'),
                        estado='programado'
                    )
                    turnos_creados += 1

            except Exception as e:
                errores.append(f"Error en fecha {fecha_str}: {str(e)}")

        return JsonResponse({
            'success': True,
            'turnos_creados': turnos_creados,
            'turnos_actualizados': turnos_actualizados,
            'turnos_existentes': turnos_existentes,
            'errores': errores
        })

    except User.DoesNotExist:
        return JsonResponse({'error': 'Operador no encontrado'}, status=404)
    except TipoTurno.DoesNotExist:
        return JsonResponse({'error': 'Tipo de turno no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def exportar_reporte_excel(request):
    """Vista para exportar reportes a Excel"""

    operador_id = request.GET.get('operador_id')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')

    if not mes or not ano:
        messages.error(request, 'Mes y año son requeridos')
        return redirect('horas_extras:reportes')

    try:
        mes = int(mes)
        ano = int(ano)

        # 1. Obtener Operadores
        if operador_id:
            operadores = User.objects.filter(id=operador_id)
        else:
            operadores = obtener_operadores_activos()

        # 2. Pre-cargar Turnos
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        fecha_inicio = date(ano, mes, 1)
        fecha_fin = date(ano, mes, ultimo_dia)
        
        # Para turnos nocturnos que cruzan medianoche (continuidad de mes)
        if mes == 1:
            fecha_busqueda_inicio = date(ano - 1, 12, 31)
        else:
            ultimo_dia_mes_anterior = calendar.monthrange(ano, mes - 1)[1]
            fecha_busqueda_inicio = date(ano, mes - 1, ultimo_dia_mes_anterior)
        
        turnos = RegistroTurno.objects.filter(
            operador__in=operadores,
            fecha__range=[fecha_busqueda_inicio, fecha_fin]
        ).select_related('tipo_turno')

        
        turnos_map = {}
        for t in turnos:
            if t.operador_id not in turnos_map:
                turnos_map[t.operador_id] = {}
            turnos_map[t.operador_id][t.fecha] = t

        # 3. Calcular
        calculadora = CalculadoraLegal()
        datos_reporte = []
        
        gran_totales = {
            'HOD': Decimal(0), 'RNO': Decimal(0),
            'RDF': Decimal(0), 'RNF': Decimal(0),
            'TOTAL': Decimal(0)
        }
        
        for operador in operadores:
            # Inicializar acumulador diario
            acumulado_diario = {}
            for d in range(1, ultimo_dia + 1):
                f = date(ano, mes, d)
                acumulado_diario[f] = {
                    'HOD': Decimal(0), 'RNO': Decimal(0), 
                    'RDF': Decimal(0), 'RNF': Decimal(0), 
                    'TOTAL': Decimal(0)
                }
            
            # Calcular horas reales
            turnos_op = [t for t in turnos if t.operador_id == operador.id]
            for turno in turnos_op:
                if turno.tipo_turno:
                    resultado = calculadora.calcular_horas_turno(turno)
                    
                    for fecha_res, horas_res in resultado.items():
                        if fecha_inicio <= fecha_res <= fecha_fin:
                            for k in ['HOD', 'RNO', 'RDF', 'RNF', 'TOTAL']:
                                acumulado_diario[fecha_res][k] += horas_res.get(k, Decimal(0))
            
            # Estructurar reporte
            info_operador = {
                'nombre': operador.get_full_name() or operador.username,
                'id': operador.id,
                'dias': [],
                'totales': {
                    'HOD': Decimal(0), 'RNO': Decimal(0), 
                    'RDF': Decimal(0), 'RNF': Decimal(0), 
                    'TOTAL': Decimal(0)
                }
            }
            
            for dia in range(1, ultimo_dia + 1):
                fecha_iter = date(ano, mes, dia)
                turno_visual = turnos_map.get(operador.id, {}).get(fecha_iter)
                
                detalle_dia = {
                    'fecha': fecha_iter,
                    'dia_semana': fecha_iter.strftime('%A'),
                    'turno': turno_visual.tipo_turno.codigo if (turno_visual and turno_visual.tipo_turno) else 'Descanso',
                    'es_festivo': calculadora.es_festivo(fecha_iter) or fecha_iter.weekday() == 6,
                    'horas': acumulado_diario.get(fecha_iter)
                }
                
                info_operador['dias'].append(detalle_dia)
                
                for k in info_operador['totales']:
                    info_operador['totales'][k] += detalle_dia['horas'][k]
            
            datos_reporte.append(info_operador)
            
            for k in gran_totales:
                gran_totales[k] += info_operador['totales'][k]
        
        # 4. Generar Excel
        periodo_str = f"{calendar.month_name[mes]} {ano}"
        return ExportadorReportes.generar_excel(datos_reporte, gran_totales, periodo_str)


    except Exception as e:
        messages.error(request, f'Error al exportar: {str(e)}')
        return redirect('horas_extras:reportes')
@login_required
def reporte_preliminar(request):
    """
    Vista para previsualizar el cálculo de nómina estricto.
    No guarda en BD, solo calcula y muestra.
    """
    hoy = date.today()
    mes = int(request.GET.get('mes', hoy.month))
    ano = int(request.GET.get('ano', hoy.year))
    
    # Obtener operadores
    operadores = obtener_operadores_activos()
    
    # Rango de fechas
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fecha_inicio = date(ano, mes, 1)
    fecha_fin = date(ano, mes, ultimo_dia)
    
    # Para turnos nocturnos que cruzan medianoche (continuidad de mes)
    if mes == 1:
        fecha_busqueda_inicio = date(ano - 1, 12, 31)
    else:
        ultimo_dia_mes_anterior = calendar.monthrange(ano, mes - 1)[1]
        fecha_busqueda_inicio = date(ano, mes - 1, ultimo_dia_mes_anterior)
    
    # Obtener turnos
    turnos = RegistroTurno.objects.filter(
        fecha__range=(fecha_busqueda_inicio, fecha_fin),
        operador__in=operadores
    ).select_related('tipo_turno', 'operador')

    
    # Indexar turnos por operador y fecha
    turnos_map = {}
    for t in turnos:
        if t.operador_id not in turnos_map:
            turnos_map[t.operador_id] = {}
        turnos_map[t.operador_id][t.fecha] = t
        
    calculadora = CalculadoraLegal()
    datos_reporte = []
    
    for operador in operadores:
        # Inicializar acumulador diario
        acumulado_diario = {}
        for d in range(1, ultimo_dia + 1):
            f = date(ano, mes, d)
            acumulado_diario[f] = {
                'HOD': Decimal(0), 'RNO': Decimal(0), 
                'RDF': Decimal(0), 'RNF': Decimal(0), 
                'TOTAL': Decimal(0)
            }
        
        # Calcular horas reales
        turnos_op = [t for t in turnos if t.operador_id == operador.id]
        for turno in turnos_op:
            if turno.tipo_turno:
                resultado = calculadora.calcular_horas_turno(turno)
                
                for fecha_res, horas_res in resultado.items():
                    if fecha_inicio <= fecha_res <= fecha_fin:
                        for k in ['HOD', 'RNO', 'RDF', 'RNF', 'TOTAL']:
                            acumulado_diario[fecha_res][k] += horas_res.get(k, Decimal(0))
        
        info_operador = {
            'nombre': operador.get_full_name() or operador.username,
            'id': operador.id,
            'dias': [],
            'totales': {
                'HOD': Decimal(0), 'RNO': Decimal(0), 
                'RDF': Decimal(0), 'RNF': Decimal(0), 
                'TOTAL': Decimal(0)
            }
        }
        
        for dia in range(1, ultimo_dia + 1):
            fecha_iter = date(ano, mes, dia)
            turno_visual = turnos_map.get(operador.id, {}).get(fecha_iter)
            
            detalle_dia = {
                'fecha': fecha_iter,
                'dia_semana': fecha_iter.strftime('%A'),
                'turno': turno_visual.tipo_turno.codigo if (turno_visual and turno_visual.tipo_turno) else 'Descanso',
                'horas': acumulado_diario.get(fecha_iter)
            }
            
            for k in info_operador['totales']:
                info_operador['totales'][k] += detalle_dia['horas'][k]
            
            info_operador['dias'].append(detalle_dia)
            
        datos_reporte.append(info_operador)

        
    context = {
        'datos': datos_reporte,
        'mes': mes,
        'ano': ano,
        'meses': [
            (i, calendar.month_name[i]) for i in range(1, 13)
        ]
    }
    
    return render(request, 'horas_extras/reporte_preliminar.html', context)
