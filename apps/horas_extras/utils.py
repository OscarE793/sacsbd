# apps/horas_extras/utils.py
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from django.db.models import Q, Sum, Count
from django.utils import timezone
import calendar
from .models import DiaFestivo, TipoTurno, RegistroTurno, CalculoRecargo, Empleado


class CalculadoraHorasExtras:
    """
    Clase principal para cálculos de horas extras y recargos
    según la legislación colombiana actualizada
    """
    
    # Porcentajes de recargos según legislación colombiana
    RECARGO_NOCTURNO = Decimal('0.35')        # 35%
    RECARGO_DOMINICAL = Decimal('0.75')       # 75%
    RECARGO_FESTIVO = Decimal('0.75')         # 75%
    RECARGO_NOCTURNO_FESTIVO = Decimal('1.10') # 110% (35% + 75%)
    
    # Porcentajes de horas extras
    HORAS_EXTRA_DIURNAS = Decimal('1.25')     # 125% (25% adicional)
    HORAS_EXTRA_NOCTURNAS = Decimal('1.75')   # 175% (75% adicional)
    HORAS_EXTRA_DOMINICALES = Decimal('2.00') # 200% (100% adicional)
    HORAS_EXTRA_FESTIVAS = Decimal('2.00')    # 200% (100% adicional)
    HORAS_EXTRA_NOCTURNAS_FESTIVAS = Decimal('2.50') # 250% (150% adicional)
    
    @classmethod
    def calcular_recargos_turno(cls, registro_turno):
        """
        Calcula todos los recargos para un turno específico
        """
        if not registro_turno.empleado.valor_hora:
            return None
        
        # Crear o actualizar cálculo
        calculo, created = CalculoRecargo.objects.get_or_create(
            registro_turno=registro_turno,
            defaults={'valor_hora_base': registro_turno.empleado.valor_hora}
        )
        
        # Realizar cálculo
        total = calculo.calcular_recargos()
        calculo.save()
        
        return calculo
    
    @classmethod
    def es_dia_festivo(cls, fecha):
        """Verifica si una fecha es día festivo en Colombia"""
        return DiaFestivo.es_festivo(fecha)
    
    @classmethod
    def obtener_horario_turno(cls, tipo_turno, fecha):
        """Obtiene el horario específico de un turno según el día de la semana"""
        return tipo_turno.get_horario_por_dia(fecha)
    
    @classmethod
    def calcular_horas_trabajadas(cls, hora_inicio, hora_fin, fecha):
        """
        Calcula las horas trabajadas entre dos horas,
        considerando turnos que cruzan medianoche
        """
        if not hora_inicio or not hora_fin:
            return Decimal('0.00')
        
        inicio = datetime.combine(fecha, hora_inicio)
        fin = datetime.combine(fecha, hora_fin)
        
        # Si el turno termina al día siguiente
        if hora_fin < hora_inicio:
            fin += timedelta(days=1)
        
        duracion = fin - inicio
        horas = Decimal(str(duracion.total_seconds() / 3600))
        
        return max(horas, Decimal('0.00'))
    
    @classmethod
    def generar_calendario_mes(cls, ano, mes):
        """
        Genera un calendario del mes con información de días festivos
        """
        primer_dia = date(ano, mes, 1)
        ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])
        
        calendario = []
        fecha_actual = primer_dia
        
        while fecha_actual <= ultimo_dia:
            dia_info = {
                'fecha': fecha_actual,
                'dia': fecha_actual.day,
                'dia_semana': fecha_actual.weekday(),
                'nombre_dia': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][fecha_actual.weekday()],
                'es_festivo': cls.es_dia_festivo(fecha_actual),
                'es_domingo': fecha_actual.weekday() == 6,
                'es_sabado': fecha_actual.weekday() == 5,
                'festivo_info': None
            }
            
            if dia_info['es_festivo']:
                try:
                    festivo = DiaFestivo.objects.get(fecha=fecha_actual, activo=True)
                    dia_info['festivo_info'] = {
                        'nombre': festivo.nombre,
                        'tipo': festivo.get_tipo_display()
                    }
                except DiaFestivo.DoesNotExist:
                    pass
            
            calendario.append(dia_info)
            fecha_actual += timedelta(days=1)
        
        return calendario


class GeneradorTurnos:
    """
    Generador de turnos rotativos para empleados del centro de cómputo
    """
    
    @classmethod
    def generar_turnos_mes(cls, empleado, ano, mes, patron_inicial='M'):
        """
        Genera turnos rotativos para un empleado durante un mes completo
        
        Patrón de rotación típico:
        - Semana 1: Mañana (M)
        - Semana 2: Tarde (T) 
        - Semana 3: Noche (N)
        - Semana 4: Descanso + Apoyo (D/A)
        """
        calendario = CalculadoraHorasExtras.generar_calendario_mes(ano, mes)
        turnos_generados = []
        
        # Obtener tipos de turno
        tipos_turno = {
            'M': TipoTurno.objects.get(codigo='M'),
            'T': TipoTurno.objects.get(codigo='T'),
            'N': TipoTurno.objects.get(codigo='N'),
            'A': TipoTurno.objects.get(codigo='A'),
            'D': TipoTurno.objects.get(codigo='D')
        }
        
        # Patrón de rotación (ejemplo básico)
        patron_rotacion = {
            'M': ['M', 'M', 'M', 'M', 'M', 'M', 'D'],  # 6 días mañana, 1 descanso
            'T': ['T', 'T', 'T', 'T', 'T', 'T', 'D'],  # 6 días tarde, 1 descanso
            'N': ['N', 'N', 'N', 'N', 'N', 'D', 'D'],  # 5 días noche, 2 descansos
            'A': ['A', 'A', 'A', 'A', 'A', 'D', 'D']   # 5 días apoyo, 2 descansos
        }
        
        patron_actual = patron_inicial
        dia_patron = 0
        
        for dia_info in calendario:
            # Determinar tipo de turno para este día
            turno_codigo = patron_rotacion[patron_actual][dia_patron % 7]
            tipo_turno = tipos_turno[turno_codigo]
            
            # Crear registro de turno
            registro = RegistroTurno(
                empleado=empleado,
                tipo_turno=tipo_turno,
                fecha=dia_info['fecha'],
                estado='programado'
            )
            
            # Obtener horarios para este día
            hora_inicio, hora_fin, horas_programadas = tipo_turno.get_horario_por_dia(dia_info['fecha'])
            
            if hora_inicio and hora_fin:
                registro.hora_inicio_real = hora_inicio
                registro.hora_fin_real = hora_fin
                registro.horas_trabajadas = horas_programadas
            
            turnos_generados.append(registro)
            dia_patron += 1
            
            # Cambiar patrón cada 7 días (rotación semanal)
            if dia_patron % 7 == 0:
                patrones = ['M', 'T', 'N', 'A']
                indice_actual = patrones.index(patron_actual)
                patron_actual = patrones[(indice_actual + 1) % len(patrones)]
        
        return turnos_generados
    
    @classmethod
    def guardar_turnos_mes(cls, turnos_list):
        """
        Guarda una lista de turnos en la base de datos
        """
        turnos_guardados = []
        
        for turno in turnos_list:
            # Verificar si ya existe un turno para esta fecha y empleado
            existente = RegistroTurno.objects.filter(
                empleado=turno.empleado,
                fecha=turno.fecha
            ).first()
            
            if existente:
                # Actualizar turno existente
                existente.tipo_turno = turno.tipo_turno
                existente.hora_inicio_real = turno.hora_inicio_real
                existente.hora_fin_real = turno.hora_fin_real
                existente.horas_trabajadas = turno.horas_trabajadas
                existente.save()
                turnos_guardados.append(existente)
            else:
                # Crear nuevo turno
                turno.save()
                turnos_guardados.append(turno)
        
        return turnos_guardados


class ReportesHorasExtras:
    """
    Generador de reportes para horas extras y recargos
    """
    
    @classmethod
    def reporte_empleado_mes(cls, empleado, ano, mes):
        """
        Genera reporte completo de un empleado para un mes específico
        """
        turnos = RegistroTurno.objects.filter(
            empleado=empleado,
            fecha__year=ano,
            fecha__month=mes,
            estado='trabajado'
        ).prefetch_related('calculo', 'tipo_turno').order_by('fecha')
        
        # Calcular totales
        total_horas = sum(turno.horas_trabajadas for turno in turnos)
        total_horas_extras = sum(turno.horas_extras for turno in turnos)
        total_turnos = len(turnos)
        
        # Calcular valores monetarios
        total_ordinario = Decimal('0.00')
        total_recargos = Decimal('0.00')
        total_horas_extras_valor = Decimal('0.00')
        
        for turno in turnos:
            if hasattr(turno, 'calculo'):
                total_ordinario += turno.calculo.total_ordinario
                total_recargos += turno.calculo.total_recargos
                total_horas_extras_valor += turno.calculo.total_horas_extras
        
        total_a_pagar = total_ordinario + total_recargos + total_horas_extras_valor
        
        # Desglose por tipo de día
        turnos_domingo = [t for t in turnos if t.es_domingo]
        turnos_festivos = [t for t in turnos if t.es_festivo]
        turnos_nocturnos = [t for t in turnos if t.incluye_nocturno]
        
        reporte = {
            'empleado': empleado,
            'periodo': f"{calendar.month_name[mes]} {ano}",
            'mes': mes,
            'ano': ano,
            'turnos': turnos,
            'resumen': {
                'total_turnos': total_turnos,
                'total_horas': total_horas,
                'total_horas_extras': total_horas_extras,
                'total_ordinario': total_ordinario,
                'total_recargos': total_recargos,
                'total_horas_extras_valor': total_horas_extras_valor,
                'total_a_pagar': total_a_pagar,
            },
            'desglose': {
                'turnos_domingo': len(turnos_domingo),
                'horas_domingos': sum(t.horas_trabajadas for t in turnos_domingo),
                'turnos_festivos': len(turnos_festivos),
                'horas_festivos': sum(t.horas_trabajadas for t in turnos_festivos),
                'turnos_nocturnos': len(turnos_nocturnos),
                'horas_nocturnas': sum(t.horas_trabajadas for t in turnos_nocturnos),
            }
        }
        
        return reporte
    
    @classmethod
    def reporte_todos_empleados_mes(cls, ano, mes):
        """
        Genera reporte de todos los empleados para un mes
        """
        empleados = Empleado.objects.filter(estado='activo').order_by('apellidos', 'nombres')
        reportes = []
        
        for empleado in empleados:
            reporte = cls.reporte_empleado_mes(empleado, ano, mes)
            reportes.append(reporte)
        
        # Calcular totales generales
        total_general = {
            'total_empleados': len(reportes),
            'total_turnos': sum(r['resumen']['total_turnos'] for r in reportes),
            'total_horas': sum(r['resumen']['total_horas'] for r in reportes),
            'total_horas_extras': sum(r['resumen']['total_horas_extras'] for r in reportes),
            'total_a_pagar': sum(r['resumen']['total_a_pagar'] for r in reportes),
        }
        
        return {
            'periodo': f"{calendar.month_name[mes]} {ano}",
            'mes': mes,
            'ano': ano,
            'empleados': reportes,
            'totales': total_general
        }
    
    @classmethod
    def calcular_todos_recargos_mes(cls, ano, mes):
        """
        Calcula los recargos para todos los turnos trabajados de un mes
        """
        turnos = RegistroTurno.objects.filter(
            fecha__year=ano,
            fecha__month=mes,
            estado='trabajado'
        ).select_related('empleado')
        
        calculados = 0
        errores = []
        
        for turno in turnos:
            try:
                CalculadoraHorasExtras.calcular_recargos_turno(turno)
                calculados += 1
            except Exception as e:
                errores.append(f"Error en turno {turno.id}: {str(e)}")
        
        return {
            'turnos_procesados': len(turnos),
            'calculados': calculados,
            'errores': errores
        }


class ValidadorTurnos:
    """
    Validaciones para turnos y horarios
    """
    
    @classmethod
    def validar_turno(cls, registro_turno):
        """
        Valida que un turno cumpla con las reglas de negocio
        """
        errores = []
        
        # Validar empleado activo
        if registro_turno.empleado.estado != 'activo':
            errores.append(f"El empleado {registro_turno.empleado} no está activo")
        
        # Validar valor hora configurado
        if not registro_turno.empleado.valor_hora:
            errores.append(f"El empleado {registro_turno.empleado} no tiene valor hora configurado")
        
        # Validar horarios
        if registro_turno.hora_inicio_real and registro_turno.hora_fin_real:
            if registro_turno.hora_inicio_real == registro_turno.hora_fin_real:
                errores.append("La hora de inicio no puede ser igual a la hora de fin")
        
        # Validar horas trabajadas máximas (12 horas por día)
        if registro_turno.horas_trabajadas > 12:
            errores.append("No se pueden trabajar más de 12 horas en un día")
        
        # Validar horas extras máximas (2 horas por día)
        if registro_turno.horas_extras > 2:
            errores.append("No se pueden trabajar más de 2 horas extras por día")
        
        # Validar duplicados
        duplicado = RegistroTurno.objects.filter(
            empleado=registro_turno.empleado,
            fecha=registro_turno.fecha
        ).exclude(id=registro_turno.id if registro_turno.id else None).exists()
        
        if duplicado:
            errores.append(f"Ya existe un turno para {registro_turno.empleado} el {registro_turno.fecha}")
        
        return errores
    
    @classmethod
    def validar_horas_extras_semana(cls, empleado, fecha):
        """
        Valida que no se excedan las 12 horas extras por semana
        """
        # Calcular inicio y fin de semana
        inicio_semana = fecha - timedelta(days=fecha.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        
        # Obtener horas extras de la semana
        horas_extras_semana = RegistroTurno.objects.filter(
            empleado=empleado,
            fecha__range=[inicio_semana, fin_semana],
            estado='trabajado'
        ).aggregate(total=Sum('horas_extras'))['total'] or Decimal('0.00')
        
        return horas_extras_semana <= 12, horas_extras_semana
