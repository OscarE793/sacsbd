# apps/horas_extras/views.py
from .exportador import ExportadorReportes
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
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

from .models import (
    Empleado, TipoTurno, DiaFestivo, RegistroTurno, 
    CalculoRecargo, ResumenMensual
)
from .utils import (
    CalculadoraHorasExtras, GeneradorTurnos, ReportesHorasExtras,
    ValidadorTurnos
)
from .forms import (
    RegistroTurnoForm, EmpleadoForm, FiltroReporteForm,
    GenerarTurnosForm
)


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
    turnos_mes = RegistroTurno.objects.filter(
        fecha__year=ano_actual,
        fecha__month=mes_actual
    )
    
    stats = {
        'total_empleados': Empleado.objects.filter(estado='activo').count(),
        'total_turnos_mes': turnos_mes.count(),
        'turnos_trabajados': turnos_mes.filter(estado='trabajado').count(),
        'turnos_pendientes': turnos_mes.filter(estado='programado').count(),
        'horas_extras_mes': turnos_mes.aggregate(
            total=Sum('horas_extras')
        )['total'] or Decimal('0.00'),
        'dias_festivos_mes': DiaFestivo.objects.filter(
            fecha__year=ano_actual,
            fecha__month=mes_actual,
            activo=True
        ).count()
    }
    
    # Empleados con más horas extras este mes
    empleados_top = RegistroTurno.objects.filter(
        fecha__year=ano_actual,
        fecha__month=mes_actual,
        estado='trabajado'
    ).values(
        'empleado__nombres', 'empleado__apellidos'
    ).annotate(
        total_horas_extras=Sum('horas_extras'),
        total_turnos=Count('id')
    ).order_by('-total_horas_extras')[:5]
    
    # Calendario del mes con festivos
    calendario = CalculadoraHorasExtras.generar_calendario_mes(ano_actual, mes_actual)
    
    # Próximos días festivos
    proximos_festivos = DiaFestivo.objects.filter(
        fecha__gte=hoy,
        activo=True
    ).order_by('fecha')[:5]
    
    context = {
        'stats': stats,
        'empleados_top': empleados_top,
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
def lista_empleados(request):
    """Vista para listar empleados"""
    
    busqueda = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    cargo = request.GET.get('cargo', '')
    
    empleados = Empleado.objects.all()
    
    if busqueda:
        empleados = empleados.filter(
            Q(nombres__icontains=busqueda) |
            Q(apellidos__icontains=busqueda) |
            Q(cedula__icontains=busqueda) |
            Q(numero_empleado__icontains=busqueda)
        )
    
    if estado:
        empleados = empleados.filter(estado=estado)
    
    if cargo:
        empleados = empleados.filter(cargo=cargo)
    
    empleados = empleados.order_by('apellidos', 'nombres')
    
    # Paginación
    paginator = Paginator(empleados, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'estado': estado,
        'cargo': cargo,
        'estados': Empleado.ESTADO_CHOICES,
        'cargos': Empleado.CARGO_CHOICES,
    }
    
    return render(request, 'horas_extras/empleados/lista.html', context)


@login_required
def detalle_empleado(request, empleado_id):
    """Vista de detalle de un empleado"""
    
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
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
        empleado=empleado,
        fecha__year=ano,
        fecha__month=mes
    ).order_by('fecha').prefetch_related('calculo', 'tipo_turno')
    
    # Generar reporte del mes
    reporte = ReportesHorasExtras.reporte_empleado_mes(empleado, ano, mes)
    
    # Resumen mensual si existe
    try:
        resumen_mensual = ResumenMensual.objects.get(
            empleado=empleado,
            mes=mes,
            ano=ano
        )
    except ResumenMensual.DoesNotExist:
        resumen_mensual = None
    
    context = {
        'empleado': empleado,
        'turnos': turnos,
        'reporte': reporte,
        'resumen_mensual': resumen_mensual,
        'mes': mes,
        'ano': ano,
        'nombre_mes': calendar.month_name[mes],
        'meses': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'anos': list(range(2024, 2030))
    }
    
    return render(request, 'horas_extras/empleados/detalle.html', context)


@login_required
def calendario_turnos(request):
    """Vista del calendario de turnos"""
    
    # Obtener mes y año
    hoy = date.today()
    mes = request.GET.get('mes', hoy.month)
    ano = request.GET.get('ano', hoy.year)
    empleado_id = request.GET.get('empleado')
    
    try:
        mes = int(mes)
        ano = int(ano)
    except (ValueError, TypeError):
        mes = hoy.month
        ano = hoy.year
    
    # Filtros
    empleados = Empleado.objects.filter(estado='activo').order_by('apellidos', 'nombres')
    empleado_seleccionado = None
    
    if empleado_id:
        try:
            empleado_seleccionado = Empleado.objects.get(id=empleado_id)
        except Empleado.DoesNotExist:
            pass
    
    # Generar calendario
    calendario = CalculadoraHorasExtras.generar_calendario_mes(ano, mes)
    
    # Obtener turnos del mes
    turnos_query = RegistroTurno.objects.filter(
        fecha__year=ano,
        fecha__month=mes
    ).select_related('empleado', 'tipo_turno')
    
    if empleado_seleccionado:
        turnos_query = turnos_query.filter(empleado=empleado_seleccionado)
    
    # Organizar turnos por fecha
    turnos_por_fecha = {}
    for turno in turnos_query:
        fecha_str = turno.fecha.strftime('%Y-%m-%d')
        if fecha_str not in turnos_por_fecha:
            turnos_por_fecha[fecha_str] = []
        turnos_por_fecha[fecha_str].append(turno)
    
    # Agregar turnos al calendario
    for dia in calendario:
        fecha_str = dia['fecha'].strftime('%Y-%m-%d')
        dia['turnos'] = turnos_por_fecha.get(fecha_str, [])
    
    context = {
        'calendario': calendario,
        'empleados': empleados,
        'empleado_seleccionado': empleado_seleccionado,
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
                
                # Calcular recargos automáticamente si el turno está trabajado
                if turno.estado == 'trabajado':
                    try:
                        CalculadoraHorasExtras.calcular_recargos_turno(turno)
                        messages.success(request, 'Recargos calculados automáticamente')
                    except Exception as e:
                        messages.warning(request, f'Error al calcular recargos: {str(e)}')
                
                return redirect('horas_extras:detalle_empleado', empleado_id=turno.empleado.id)
    else:
        # Pre-llenar con empleado y fecha si se proporcionan
        empleado_id = request.GET.get('empleado')
        fecha = request.GET.get('fecha')
        
        initial = {}
        if empleado_id:
            try:
                empleado = Empleado.objects.get(id=empleado_id)
                initial['empleado'] = empleado
            except Empleado.DoesNotExist:
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
                
                # Recalcular recargos si el turno está trabajado
                if turno_actualizado.estado == 'trabajado':
                    try:
                        CalculadoraHorasExtras.calcular_recargos_turno(turno_actualizado)
                        messages.success(request, 'Recargos recalculados automáticamente')
                    except Exception as e:
                        messages.warning(request, f'Error al recalcular recargos: {str(e)}')
                
                return redirect('horas_extras:detalle_empleado', empleado_id=turno.empleado.id)
    else:
        form = RegistroTurnoForm(instance=turno)
    
    context = {
        'form': form,
        'turno': turno,
        'title': f'Editar Turno - {turno.empleado.nombres} ({turno.fecha})'
    }
    
    return render(request, 'horas_extras/turnos/form.html', context)


@login_required
def generar_turnos_automaticos(request):
    """Vista para generar turnos automáticos"""
    
    if request.method == 'POST':
        form = GenerarTurnosForm(request.POST)
        if form.is_valid():
            empleado = form.cleaned_data['empleado']
            mes = form.cleaned_data['mes']
            ano = form.cleaned_data['ano']
            patron_inicial = form.cleaned_data['patron_inicial']
            sobrescribir = form.cleaned_data['sobrescribir']
            
            try:
                # Verificar si ya existen turnos
                turnos_existentes = RegistroTurno.objects.filter(
                    empleado=empleado,
                    fecha__year=ano,
                    fecha__month=mes
                ).count()
                
                if turnos_existentes > 0 and not sobrescribir:
                    messages.warning(
                        request,
                        f'Ya existen {turnos_existentes} turnos para {empleado.nombres} en {calendar.month_name[mes]} {ano}. '
                        'Marque "Sobrescribir existentes" para reemplazarlos.'
                    )
                else:
                    # Eliminar turnos existentes si se va a sobrescribir
                    if sobrescribir:
                        RegistroTurno.objects.filter(
                            empleado=empleado,
                            fecha__year=ano,
                            fecha__month=mes
                        ).delete()
                    
                    # Generar nuevos turnos
                    turnos_nuevos = GeneradorTurnos.generar_turnos_mes(
                        empleado, ano, mes, patron_inicial
                    )
                    
                    # Guardar turnos
                    turnos_guardados = GeneradorTurnos.guardar_turnos_mes(turnos_nuevos)
                    
                    messages.success(
                        request,
                        f'Se generaron {len(turnos_guardados)} turnos para {empleado.nombres} '
                        f'en {calendar.month_name[mes]} {ano}'
                    )
                    
                    return redirect('horas_extras:detalle_empleado', empleado_id=empleado.id)
                    
            except Exception as e:
                messages.error(request, f'Error al generar turnos: {str(e)}')
    else:
        # Pre-llenar con empleado si se proporciona
        empleado_id = request.GET.get('empleado')
        initial = {}
        
        if empleado_id:
            try:
                empleado = Empleado.objects.get(id=empleado_id)
                initial['empleado'] = empleado
            except Empleado.DoesNotExist:
                pass
        
        # Mes y año actuales
        hoy = date.today()
        initial.update({
            'mes': hoy.month,
            'ano': hoy.year
        })
        
        form = GenerarTurnosForm(initial=initial)
    
    context = {
        'form': form,
        'title': 'Generar Turnos Automáticos'
    }
    
    return render(request, 'horas_extras/turnos/generar.html', context)


@login_required
def reportes_horas_extras(request):
    """Vista para reportes de horas extras"""
    
    if request.method == 'POST':
        form = FiltroReporteForm(request.POST)
        if form.is_valid():
            empleado = form.cleaned_data.get('empleado')
            mes = form.cleaned_data['mes']
            ano = form.cleaned_data['ano']
            tipo_reporte = form.cleaned_data['tipo_reporte']
            
            if tipo_reporte == 'individual' and empleado:
                # Reporte individual
                reporte = ReportesHorasExtras.reporte_empleado_mes(empleado, ano, mes)
                
                context = {
                    'reporte': reporte,
                    'tipo': 'individual',
                    'form': form
                }
                
                return render(request, 'horas_extras/reportes/resultado.html', context)
                
            elif tipo_reporte == 'todos':
                # Reporte de todos los empleados
                reporte = ReportesHorasExtras.reporte_todos_empleados_mes(ano, mes)
                
                context = {
                    'reporte': reporte,
                    'tipo': 'todos',
                    'form': form
                }
                
                return render(request, 'horas_extras/reportes/resultado.html', context)
    else:
        # Valores por defecto
        hoy = date.today()
        form = FiltroReporteForm(initial={
            'mes': hoy.month,
            'ano': hoy.year,
            'tipo_reporte': 'todos'
        })
    
    context = {
        'form': form,
        'title': 'Reportes de Horas Extras'
    }
    
    return render(request, 'horas_extras/reportes/filtro.html', context)


@login_required
@require_http_methods(["POST"])
def calcular_recargos_lote(request):
    """Vista para calcular recargos en lote"""
    
    mes = request.POST.get('mes')
    ano = request.POST.get('ano')
    empleado_id = request.POST.get('empleado_id')
    
    if not mes or not ano:
        return JsonResponse({'error': 'Mes y año son requeridos'}, status=400)
    
    try:
        mes = int(mes)
        ano = int(ano)
    except ValueError:
        return JsonResponse({'error': 'Mes y año deben ser números'}, status=400)
    
    try:
        if empleado_id:
            # Calcular para un empleado específico
            empleado = Empleado.objects.get(id=empleado_id)
            turnos = RegistroTurno.objects.filter(
                empleado=empleado,
                fecha__year=ano,
                fecha__month=mes,
                estado='trabajado'
            )
        else:
            # Calcular para todos los empleados
            turnos = RegistroTurno.objects.filter(
                fecha__year=ano,
                fecha__month=mes,
                estado='trabajado'
            )
        
        calculados = 0
        errores = []
        
        for turno in turnos:
            try:
                CalculadoraHorasExtras.calcular_recargos_turno(turno)
                calculados += 1
            except Exception as e:
                errores.append(f"Error en turno {turno.id}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'calculados': calculados,
            'total_turnos': len(turnos),
            'errores': errores
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
    """Vista AJAX para obtener datos del calendario"""
    
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    empleado_id = request.GET.get('empleado_id')
    
    if not mes or not ano:
        return JsonResponse({'error': 'Mes y año son requeridos'}, status=400)
    
    try:
        mes = int(mes)
        ano = int(ano)
        
        # Generar calendario
        calendario = CalculadoraHorasExtras.generar_calendario_mes(ano, mes)
        
        # Obtener turnos
        turnos_query = RegistroTurno.objects.filter(
            fecha__year=ano,
            fecha__month=mes
        ).select_related('empleado', 'tipo_turno')
        
        if empleado_id:
            turnos_query = turnos_query.filter(empleado_id=empleado_id)
        
        # Organizar turnos por fecha
        turnos_por_fecha = {}
        for turno in turnos_query:
            fecha_str = turno.fecha.strftime('%Y-%m-%d')
            if fecha_str not in turnos_por_fecha:
                turnos_por_fecha[fecha_str] = []
            
            turnos_por_fecha[fecha_str].append({
                'id': turno.id,
                'empleado': f"{turno.empleado.nombres} {turno.empleado.apellidos}",
                'tipo_turno': turno.tipo_turno.codigo,
                'estado': turno.estado,
                'horas_trabajadas': str(turno.horas_trabajadas),
                'horas_extras': str(turno.horas_extras)
            })
        
        # Preparar respuesta
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
                'festivo_info': dia['festivo_info'],
                'turnos': turnos_por_fecha.get(fecha_str, [])
            })
        
        return JsonResponse({
            'calendario': calendar_data,
            'mes': mes,
            'ano': ano,
            'nombre_mes': calendar.month_name[mes]
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def exportar_reporte_excel(request):
    """Vista para exportar reportes a Excel"""
    
    empleado_id = request.GET.get('empleado_id')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    
    if not mes or not ano:
        messages.error(request, 'Mes y año son requeridos')
        return redirect('horas_extras:reportes')
    try:
        mes = int(mes)
        ano = int(ano)
        if empleado_id:
            # Reporte individual
            empleado = get_object_or_404(Empleado, id=empleado_id)
            reporte = ReportesHorasExtras.reporte_empleado_mes(empleado, ano, mes)
            return ExportadorReportes.exportar_excel_empleado(reporte)
        else:
            # Reporte de todos
            reporte = ReportesHorasExtras.reporte_todos_empleados_mes(ano, mes)
            return ExportadorReportes.exportar_excel_todos(reporte)
    except Exception as e:
        messages.error(request, f'Error al exportar: {str(e)}')
        return redirect('horas_extras:reportes')
