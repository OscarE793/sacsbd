# apps/horas_extras/utils.py - VERSIÓN SIMPLIFICADA
# Sistema SOLO calcula horas, no valores monetarios

from decimal import Decimal
from datetime import datetime, date, time, timedelta
from django.db.models import Q, Sum, Count
from django.contrib.auth.models import User
from django.utils import timezone
import calendar

from .models import DiaFestivo, TipoTurno, RegistroTurno, ResumenMensual
from apps.user_management.models import Role, UserRole


class CalculadoraHorasExtras:
    """
    Clase para cálculos de horas trabajadas
    Sistema SIMPLIFICADO: Solo calcula horas, NO valores monetarios
    """

    @classmethod
    def es_dia_festivo(cls, fecha):
        """Verifica si una fecha es día festivo en Colombia usando librería holidays"""
        import holidays
        co_holidays = holidays.CO()
        return fecha in co_holidays

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
    Generador de turnos rotativos para operadores del centro de cómputo
    Rotación semanal de Miércoles a Martes
    """

    @classmethod
    def generar_turnos_mes(cls, operador, ano, mes, turno_inicial='Turno 1-M', es_inicio_ciclo_n=None):
        """
        Genera turnos rotativos para un operador durante un mes completo

        Patrón de rotación (cambia cada MIÉRCOLES):
        - Semana 1 (Mié-Mar): Apoyo-A (solo Lun-Vie)
        - Semana 2 (Mié-Mar): Turno 1-M (Mañana, todos los días)
        - Semana 3 (Mié-Mar): Turno 2-T (Tarde, todos los días)
        - Semana 4 (Mié-Mar): Turno 3-N (Noche, todos los días)
        - Ciclo se repite

        REGLAS ESPECIALES PARA TURNO NOCTURNO (Turno 3-N):
        - PRIMER miércoles del ciclo N: 23:00-23:59 (1 hora)
        - Días intermedios (Jue-Mar): 23:00-06:00 (7 horas)
        - ÚLTIMO miércoles (transición a siguiente turno): 00:00-06:00 (6 horas)
        
        Args:
            operador: User (operador) al que se asignarán los turnos
            ano: Año del calendario
            mes: Mes del calendario (1-12)
            turno_inicial: Código del turno inicial (ej: 'Turno 1-M', 'Apoyo-A', etc.)
            es_inicio_ciclo_n: None = auto-detect, True = forzar primer día como inicio de N
        """
        from datetime import time
        
        calendario = CalculadoraHorasExtras.generar_calendario_mes(ano, mes)
        turnos_generados = []

        # Obtener tipos de turno por código REAL de la base de datos
        try:
            tipos_turno = {
                'A': TipoTurno.objects.get(codigo='A'),  # Apoyo
                'M': TipoTurno.objects.get(codigo='M'),  # Mañana
                'T': TipoTurno.objects.get(codigo='T'),  # Tarde
                'N': TipoTurno.objects.get(codigo='N'),  # Noche
                'D': TipoTurno.objects.get(codigo='D')   # Descanso
            }
        except TipoTurno.DoesNotExist as e:
            # Listar tipos disponibles para debug
            disponibles = list(TipoTurno.objects.values_list('codigo', flat=True))
            raise ValueError(
                f"Error: Falta algún tipo de turno requerido. "
                f"Códigos disponibles en DB: {disponibles}. "
                f"Se requieren: A, M, T, N, D"
            )

        # Orden de rotación semanal para Oscar (Miércoles a Martes)
        # Basado en datos reales: T → N → D → M → T → ...
        # NOTA: D (Descanso) es parte de la rotación normal, no solo un fallback
        orden_rotacion = ['T', 'N', 'D', 'M']

        # Encontrar el índice del turno inicial
        if turno_inicial not in orden_rotacion:
            turno_inicial = 'M'  # Default a Mañana

        indice_turno_actual = orden_rotacion.index(turno_inicial)
        turno_actual_codigo = turno_inicial
        turno_anterior_codigo = None

        # Contador de días desde el último miércoles de cambio de turno
        dias_desde_miercoles = 0
        
        # Flag para tracking de ciclo N
        # Si es_inicio_ciclo_n es True, significa que el mes empieza CON el ciclo N ya activo
        # En ese caso, el primer miércoles NO debe rotar, es el PRIMER miércoles del ciclo
        primer_miercoles_del_ciclo_inicial = False
        if es_inicio_ciclo_n is True:
            primer_miercoles_del_ciclo_inicial = True
        
        primer_miercoles_n_ya_paso = False
        if turno_inicial == 'N' and es_inicio_ciclo_n is False:
            primer_miercoles_n_ya_paso = True

        for i, dia_info in enumerate(calendario):
            dia_semana = dia_info['dia_semana']  # 0=Lun, 1=Mar, 2=Mié, 3=Jue, 4=Vie, 5=Sáb, 6=Dom
            fecha = dia_info['fecha']

            # Guardar turno anterior ANTES de la rotación
            turno_anterior_codigo = turno_actual_codigo
            
            # Detectar cambio de turno (cada miércoles después del primero del ciclo)
            cambio_turno_hoy = False
            
            # Si es el primer miércoles del ciclo inicial, NO rotar
            if dia_semana == 2 and primer_miercoles_del_ciclo_inicial:
                primer_miercoles_del_ciclo_inicial = False
                dias_desde_miercoles = 0
            elif dia_semana == 2 and dias_desde_miercoles > 0:
                # Miércoles de rotación normal
                indice_turno_actual = (indice_turno_actual + 1) % len(orden_rotacion)
                turno_actual_codigo = orden_rotacion[indice_turno_actual]
                dias_desde_miercoles = 0
                cambio_turno_hoy = True
                
                # Si acabamos de entrar al ciclo N, resetear el flag
                if turno_actual_codigo == 'N':
                    primer_miercoles_n_ya_paso = False

            # Determinar el tipo de turno para este día
            tipo_turno = tipos_turno[turno_actual_codigo]

            # Obtener horarios por defecto para este día
            hora_inicio, hora_fin, horas_programadas = tipo_turno.get_horario_por_dia(fecha)

            # ========== REGLAS ESPECIALES ==========
            
            # CASO 1: Miércoles de TRANSICIÓN desde N hacia D
            # El último miércoles del ciclo N muestra 6h (spillover del martes)
            if cambio_turno_hoy and turno_anterior_codigo == 'N':
                # Este miércoles todavía se muestra como N (6h spillover)
                tipo_turno = tipos_turno['N']
                hora_inicio = time(0, 0)
                hora_fin = time(6, 0)
                horas_programadas = Decimal('6.00')


            # CASO 2: Apoyo en fin de semana = Descanso
            elif turno_actual_codigo == 'A' and dia_semana in [5, 6]:
                tipo_turno = tipos_turno['D']
                hora_inicio, hora_fin, horas_programadas = None, None, Decimal('0.00')

            
            # CASO 3: Turno Nocturno (N) - lógica especial
            elif turno_actual_codigo == 'N':
                # Detectar si es el PRIMER miércoles del ciclo N
                es_primer_miercoles_n = False
                
                if dia_semana == 2:  # Es miércoles
                    if cambio_turno_hoy:
                        # Acabamos de cambiar A turno N este miércoles
                        # Este ES el primer miércoles del ciclo N
                        es_primer_miercoles_n = True
                    elif not primer_miercoles_n_ya_paso and dias_desde_miercoles == 0 and i == 0:
                        # Es el primer día del mes, es miércoles, estamos en N
                        # Y el flag indica que es inicio del ciclo
                        es_primer_miercoles_n = True
                
                if es_primer_miercoles_n:
                    # PRIMER miércoles del ciclo N: solo 23:00-23:59 (1 hora)
                    hora_inicio = time(23, 0)
                    hora_fin = time(23, 59)
                    horas_programadas = Decimal('1.00')
                    primer_miercoles_n_ya_paso = True
                else:
                    # Días intermedios (Jue-Mar) o miércoles no-primero: 23:00-06:00 (7 horas)
                    hora_inicio = time(23, 0)
                    hora_fin = time(6, 0)
                    horas_programadas = Decimal('7.00')
                    primer_miercoles_n_ya_paso = True


            # Crear registro de turno
            registro = RegistroTurno(
                operador=operador,
                tipo_turno=tipo_turno,
                fecha=fecha,
                estado='programado',
                hora_inicio_real=hora_inicio,
                hora_fin_real=hora_fin,
                horas_trabajadas=horas_programadas or Decimal('0.00')
            )

            turnos_generados.append(registro)
            dias_desde_miercoles += 1

        return turnos_generados



    @classmethod
    def guardar_turnos_mes(cls, turnos_list):
        """
        Guarda una lista de turnos en la base de datos
        """
        turnos_guardados = []

        for turno in turnos_list:
            # Verificar si ya existe un turno para esta fecha y operador
            existente = RegistroTurno.objects.filter(
                operador=turno.operador,
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

    @classmethod
    def generar_turnos_operador_v3(cls, operador, fecha_inicio, fecha_fin):
        """
        Genera turnos usando lógica de VECINDAD para turno N.
        
        SOPORTA MÚLTIPLES SEEDS POR OPERADOR:
        - Para cada fecha, busca el seed vigente (fecha_inicio <= fecha)
        - Permite cambios de patrón por vacaciones, reubicaciones, etc.
        
        REGLA DE VECINDAD PARA HORAS N:
        - prev_is_N = turno(fecha-1) == 'N'
        - today_is_N = turno(fecha) == 'N'
        - next_is_N = turno(fecha+1) == 'N'
        
        madrugada = 6 if prev_is_N else 0  (00:00-06:00)
        noche = (1 o 2) if today_is_N AND next_is_N else 0
            - noche = 2 si Sáb/Dom/Lun
            - noche = 1 si Mar-Vie
        
        horas_trabajadas = madrugada + noche
        """
        from datetime import time, timedelta
        from apps.horas_extras.models import TipoTurno, RegistroTurno, PatronOperador
        
        # Obtener tipos de turno
        try:
            tipos_turno = {
                'T': TipoTurno.objects.get(codigo='T'),
                'N': TipoTurno.objects.get(codigo='N'),
                'D': TipoTurno.objects.get(codigo='D'),
                'M': TipoTurno.objects.get(codigo='M'),
                'A': TipoTurno.objects.get(codigo='A'),
            }
        except TipoTurno.DoesNotExist:
            disponibles = list(TipoTurno.objects.values_list('codigo', flat=True))
            raise ValueError(f"Falta algún tipo de turno. Disponibles: {disponibles}")
        
        # Verificar que existe al menos un seed
        if not PatronOperador.objects.filter(operador=operador).exists():
            raise ValueError(
                f"No existe PatronOperador para {operador.get_full_name()}. "
                f"Use: set_patron_operador --operador {operador.username} --fecha YYYY-MM-DD --turno T/N/D/M"
            )
        
        # Función helper: obtener turno de una fecha usando seed vigente
        def turno_de_fecha(fecha):
            return PatronOperador.calcular_turno_para_fecha(operador, fecha)

        
        turnos_generados = []
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            dia_semana = fecha_actual.weekday()  # 0=Lun, 6=Dom
            
            # Calcular turnos de vecindad
            turno_ayer = turno_de_fecha(fecha_actual - timedelta(days=1))
            turno_hoy = turno_de_fecha(fecha_actual)
            turno_manana = turno_de_fecha(fecha_actual + timedelta(days=1))
            
            prev_is_N = (turno_ayer == 'N')
            today_is_N = (turno_hoy == 'N')
            next_is_N = (turno_manana == 'N')
            
            tipo_turno = tipos_turno[turno_hoy]
            hora_inicio = None
            hora_fin = None
            horas_trabajadas = Decimal('0.00')
            
            if turno_hoy == 'N':
                # ===== LÓGICA DE VECINDAD PARA TURNO N =====
                
                # Madrugada: 00:00-06:00 (viene del turno iniciado ayer)
                madrugada = 6 if prev_is_N else 0
                
                # Noche: 22:00-24:00 o 23:00-24:00 (inicia hoy, continúa mañana)
                if today_is_N and next_is_N:
                    if dia_semana in [5, 6, 0]:  # Sáb, Dom, Lun
                        noche = 2
                    else:  # Mar-Vie
                        noche = 1
                else:
                    noche = 0
                
                horas_trabajadas = Decimal(str(madrugada + noche))
                
                # Establecer hora_inicio_real y hora_fin_real según el caso
                if madrugada > 0 and noche > 0:
                    # Día normal N: 00:00-06:00 + 23:00-24:00
                    hora_inicio = time(23, 0)
                    hora_fin = time(6, 0)
                elif madrugada > 0 and noche == 0:
                    # Último día del bloque N: solo madrugada
                    hora_inicio = time(0, 0)
                    hora_fin = time(6, 0)
                elif madrugada == 0 and noche > 0:
                    # Primer día del bloque N: solo noche
                    if noche == 2:
                        hora_inicio = time(22, 0)
                    else:
                        hora_inicio = time(23, 0)
                    hora_fin = time(23, 59)
                    
            elif turno_hoy == 'D':
                # Descanso
                hora_inicio = None
                hora_fin = None
                horas_trabajadas = Decimal('0.00')
                
            elif turno_hoy == 'M':
                # Mañana: 06:00-14:00
                hora_inicio = time(6, 0)
                hora_fin = time(14, 0)
                if dia_semana in [5, 6, 0]:  # Sáb, Dom, Lun
                    horas_trabajadas = Decimal('8.00')
                else:
                    horas_trabajadas = Decimal('7.00')
                    
            elif turno_hoy == 'T':
                # Tarde: 14:00-22:00
                hora_inicio = time(14, 0)
                hora_fin = time(22, 0)
                if dia_semana in [5, 6, 0]:  # Sáb, Dom, Lun
                    horas_trabajadas = Decimal('8.00')
                else:
                    horas_trabajadas = Decimal('7.00')
                    
            elif turno_hoy == 'A':
                # Apoyo: 13:00-21:00
                hora_inicio = time(13, 0)
                hora_fin = time(21, 0)
                horas_trabajadas = Decimal('8.00')
            
            # Crear registro de turno
            registro = RegistroTurno(
                operador=operador,
                tipo_turno=tipo_turno,
                fecha=fecha_actual,
                estado='programado',
                hora_inicio_real=hora_inicio,
                hora_fin_real=hora_fin,
                horas_trabajadas=horas_trabajadas
            )
            
            turnos_generados.append(registro)
            fecha_actual += timedelta(days=1)
        
        return turnos_generados

    @classmethod
    def generar_turnos_rango(cls, operador, fecha_inicio, fecha_fin, turno_inicio_ciclo='T', 

                              fecha_inicio_ciclo=None):
        """
        Genera turnos de forma CONTINUA para un rango de fechas.
        
        REGLA FUNDAMENTAL:
        El ciclo se evalúa por fecha absoluta continua, no por mes ni por año.
        El 31/12 y el 01/01 pertenecen al mismo ciclo si no hay transición.
        
        TURNOS ESPECIALES DEL CICLO N:
        | Caso                  | hora_inicio_real | hora_fin_real | horas_trabajadas |
        |-----------------------|------------------|---------------|------------------|
        | Primer miércoles N    | 23:00            | 23:59         | 1                |
        | Día intermedio N      | 23:00            | 06:00         | 7                |
        | Último miércoles N    | 00:00            | 06:00         | 6                |
        | Día D                 | NULL             | NULL          | 0                |
        
        Args:
            operador: User al que se asignarán los turnos
            fecha_inicio: date - primera fecha del rango
            fecha_fin: date - última fecha del rango (inclusive)
            turno_inicio_ciclo: Código del turno que INICIA en fecha_inicio_ciclo
            fecha_inicio_ciclo: date - miércoles en que comenzó el ciclo actual
                               Si None, se asume que fecha_inicio es un miércoles de inicio
        """
        from datetime import time, timedelta
        from apps.horas_extras.models import TipoTurno, RegistroTurno
        
        # Obtener tipos de turno
        try:
            tipos_turno = {
                'T': TipoTurno.objects.get(codigo='T'),
                'N': TipoTurno.objects.get(codigo='N'),
                'D': TipoTurno.objects.get(codigo='D'),
                'M': TipoTurno.objects.get(codigo='M'),
            }
        except TipoTurno.DoesNotExist:
            disponibles = list(TipoTurno.objects.values_list('codigo', flat=True))
            raise ValueError(f"Falta algún tipo de turno. Disponibles: {disponibles}")
        
        # Orden de rotación con duraciones REALES:
        # T: 7 días (Wed-Tue)
        # N: 8 días (Wed-Wed) - incluye último mié con 6h
        # D: 6 días (Thu-Tue) - empieza jueves después de N
        # M: 7 días (Wed-Tue)
        # TOTAL CICLO = 28 días
        
        ciclos_config = [
            ('T', 7),   # 0-6 días
            ('N', 8),   # 7-14 días (incluye último mié)
            ('D', 6),   # 15-20 días
            ('M', 7),   # 21-27 días
        ]
        ciclo_total = sum(c[1] for c in ciclos_config)  # 28 días
        
        # Determinar el miércoles de referencia para el ciclo
        if fecha_inicio_ciclo is None:
            # Buscar el miércoles anterior o igual a fecha_inicio
            dias_hasta_mie = (fecha_inicio.weekday() - 2) % 7
            fecha_inicio_ciclo = fecha_inicio - timedelta(days=dias_hasta_mie)
        
        # Calcular offset inicial basado en turno_inicio_ciclo
        offset_inicial = 0
        for codigo, duracion in ciclos_config:
            if codigo == turno_inicio_ciclo:
                break
            offset_inicial += duracion
        
        turnos_generados = []
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            dia_semana = fecha_actual.weekday()  # 0=Lun, 2=Mié
            
            # Calcular posición absoluta en el ciclo de 28 días
            dias_desde_inicio = (fecha_actual - fecha_inicio_ciclo).days
            pos_en_ciclo_28 = (dias_desde_inicio + offset_inicial) % ciclo_total
            
            # Determinar en qué turno estamos y posición dentro de ese turno
            turno_actual = None
            dia_en_turno = 0
            pos_acumulada = 0
            
            for codigo, duracion in ciclos_config:
                if pos_en_ciclo_28 < pos_acumulada + duracion:
                    turno_actual = codigo
                    dia_en_turno = pos_en_ciclo_28 - pos_acumulada
                    break
                pos_acumulada += duracion
            
            # ========== ASIGNAR TIPO DE TURNO Y HORAS ==========
            
            tipo_turno = tipos_turno[turno_actual]
            hora_inicio = None
            hora_fin = None
            horas_trabajadas = Decimal('0.00')
            
            if turno_actual == 'N':
                # ===== LÓGICA ESPECIAL PARA TURNO N (8 días) =====
                # día 0: Primer Mié (23:00-23:59, 1h)
                # días 1-6: Jue-Mar (23:00-06:00, 7h)
                # día 7: Último Mié (00:00-06:00, 6h)
                
                if dia_en_turno == 0:
                    # PRIMER miércoles del ciclo N
                    hora_inicio = time(23, 0)
                    hora_fin = time(23, 59)
                    horas_trabajadas = Decimal('1.00')
                elif dia_en_turno == 7:
                    # ÚLTIMO miércoles del ciclo N (día 8)
                    hora_inicio = time(0, 0)
                    hora_fin = time(6, 0)
                    horas_trabajadas = Decimal('6.00')
                else:
                    # Días intermedios: 23:00-06:00 = 7h
                    hora_inicio = time(23, 0)
                    hora_fin = time(6, 0)
                    horas_trabajadas = Decimal('7.00')
                    
            elif turno_actual == 'D':
                # Descanso (6 días: Thu-Tue)
                hora_inicio = None
                hora_fin = None
                horas_trabajadas = Decimal('0.00')
                
            elif turno_actual == 'M':
                # Mañana: 06:00-14:00
                hora_inicio = time(6, 0)
                hora_fin = time(14, 0)
                # Mar-Vie = 7h, Sáb-Lun = 8h
                if dia_semana in [5, 6, 0]:  # Sáb, Dom, Lun
                    horas_trabajadas = Decimal('8.00')
                else:
                    horas_trabajadas = Decimal('7.00')
                    
            elif turno_actual == 'T':
                # Tarde: 14:00-22:00
                hora_inicio = time(14, 0)
                hora_fin = time(22, 0)
                # Mar-Vie = 7h, Sáb-Lun = 8h
                if dia_semana in [5, 6, 0]:  # Sáb, Dom, Lun
                    horas_trabajadas = Decimal('8.00')
                else:
                    horas_trabajadas = Decimal('7.00')
            
            # Crear registro de turno
            registro = RegistroTurno(
                operador=operador,
                tipo_turno=tipo_turno,
                fecha=fecha_actual,
                estado='programado',
                hora_inicio_real=hora_inicio,
                hora_fin_real=hora_fin,
                horas_trabajadas=horas_trabajadas
            )
            
            turnos_generados.append(registro)
            fecha_actual += timedelta(days=1)
        
        return turnos_generados



class ReportesHorasExtras:
    """
    Generador de reportes para horas trabajadas
    IMPORTANTE: Solo reporta HORAS, no valores monetarios
    """

    @classmethod
    def reporte_operador_mes(cls, operador, ano, mes):

        """
        Genera reporte completo de un operador para un mes específico
        SOLO HORAS, sin cálculos monetarios
        """
        turnos = RegistroTurno.objects.filter(
            operador=operador,
            fecha__year=ano,
            fecha__month=mes,
            estado='trabajado'
        ).select_related('tipo_turno').order_by('fecha')

        # Calcular totales de horas SOLAMENTE
        total_horas = sum(turno.horas_trabajadas for turno in turnos)
        total_turnos = len(turnos)

        # Desglose por tipo de día (solo horas)
        turnos_lunes = [t for t in turnos if t.es_lunes]
        turnos_martes = [t for t in turnos if t.es_martes]
        turnos_miercoles = [t for t in turnos if t.es_miercoles]
        turnos_jueves = [t for t in turnos if t.es_jueves]
        turnos_viernes = [t for t in turnos if t.es_viernes]
        turnos_sabados = [t for t in turnos if t.es_sabado]
        turnos_domingo = [t for t in turnos if t.es_domingo]
        turnos_festivos = [t for t in turnos if t.es_festivo]
        turnos_nocturnos = [t for t in turnos if t.incluye_nocturno]

        reporte = {
            'operador': operador,
            'periodo': f"{calendar.month_name[mes]} {ano}",
            'mes': mes,
            'ano': ano,
            'turnos': turnos,
            'resumen': {
                'total_turnos': total_turnos,
                'total_horas': total_horas,
            },
            'desglose': {
                'horas_lunes': sum(t.horas_trabajadas for t in turnos_lunes),
                'horas_martes': sum(t.horas_trabajadas for t in turnos_martes),
                'horas_miercoles': sum(t.horas_trabajadas for t in turnos_miercoles),
                'horas_jueves': sum(t.horas_trabajadas for t in turnos_jueves),
                'horas_viernes': sum(t.horas_trabajadas for t in turnos_viernes),
                'horas_sabados': sum(t.horas_trabajadas for t in turnos_sabados),
                'horas_domingos': sum(t.horas_trabajadas for t in turnos_domingo),
                'horas_festivos': sum(t.horas_trabajadas for t in turnos_festivos),
                'horas_nocturnas': sum(t.horas_trabajadas for t in turnos_nocturnos),
                'turnos_domingo': len(turnos_domingo),
                'turnos_festivos': len(turnos_festivos),
                'turnos_nocturnos': len(turnos_nocturnos),
            }
        }

        return reporte

    @classmethod
    def reporte_todos_operadores_mes(cls, ano, mes):
        """
        Genera reporte de todos los operadores activos para un mes
        SOLO HORAS, sin cálculos monetarios
        """
        # Obtener operadores con rol "operador de centro de computo"
        try:
            rol_operador = Role.objects.get(name='operador de centro de computo')
            operadores = User.objects.filter(
                is_active=True,
                userrole__role=rol_operador,
                userrole__activo=True
            ).distinct().order_by('last_name', 'first_name')
        except Role.DoesNotExist:
            operadores = User.objects.none()

        reportes = []

        for operador in operadores:
            reporte = cls.reporte_operador_mes(operador, ano, mes)
            reportes.append(reporte)

        # Calcular totales generales (solo horas)
        total_general = {
            'total_operadores': len(reportes),
            'total_turnos': sum(r['resumen']['total_turnos'] for r in reportes),
            'total_horas': sum(r['resumen']['total_horas'] for r in reportes),
        }

        return {
            'periodo': f"{calendar.month_name[mes]} {ano}",
            'mes': mes,
            'ano': ano,
            'operadores': reportes,
            'totales': total_general
        }

    @classmethod
    def generar_resumen_mensual(cls, operador, ano, mes):
        """
        Genera o actualiza el resumen mensual para un operador
        Este resumen se envía a nómina
        """
        resumen, created = ResumenMensual.objects.get_or_create(
            operador=operador,
            mes=mes,
            ano=ano
        )

        # Calcular y guardar
        resumen.calcular_resumen()

        return resumen


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

        # Validar operador activo
        if not registro_turno.operador.is_active:
            errores.append(f"El operador {registro_turno.operador.get_full_name()} no está activo")

        # Validar que tiene rol de operador
        try:
            rol_operador = Role.objects.get(name='operador de centro de computo')
            if not UserRole.objects.filter(
                user=registro_turno.operador,
                role=rol_operador,
                activo=True
            ).exists():
                errores.append(f"El usuario {registro_turno.operador.username} no tiene el rol de operador de centro de cómputo")
        except Role.DoesNotExist:
            errores.append("El rol 'operador de centro de computo' no está configurado en el sistema")

        # Validar horarios
        if registro_turno.hora_inicio_real and registro_turno.hora_fin_real:
            if registro_turno.hora_inicio_real == registro_turno.hora_fin_real:
                errores.append("La hora de inicio no puede ser igual a la hora de fin")

        # Validar horas trabajadas máximas (12 horas por día)
        if registro_turno.horas_trabajadas > 12:
            errores.append("No se pueden trabajar más de 12 horas en un día")

        # Validar duplicados
        duplicado = RegistroTurno.objects.filter(
            operador=registro_turno.operador,
            fecha=registro_turno.fecha
        ).exclude(id=registro_turno.id if registro_turno.id else None).exists()

        if duplicado:
            errores.append(f"Ya existe un turno para {registro_turno.operador.get_full_name()} el {registro_turno.fecha}")

        return errores

    @classmethod
    def validar_horas_semana(cls, operador, fecha):
        """
        Valida horas trabajadas en la semana
        """
        # Calcular inicio y fin de semana
        inicio_semana = fecha - timedelta(days=fecha.weekday())
        fin_semana = inicio_semana + timedelta(days=6)

        # Obtener horas de la semana
        horas_semana = RegistroTurno.objects.filter(
            operador=operador,
            fecha__range=[inicio_semana, fin_semana],
            estado='trabajado'
        ).aggregate(total=Sum('horas_trabajadas'))['total'] or Decimal('0.00')

        return horas_semana


class GeneradorTurnosV4:
    """
    Generador V4: Rangos horarios reales por turno + día de semana.
    
    REGLAS:
    1. Cada turno tiene horario diferente según día de la semana
    2. RNO inicia según ParametroNormativo (19:00 post-reforma, 21:00 pre-reforma)
    3. Turno N devuelve segmentos reales (no solo horas)
    4. Turno A no trabaja sábados, domingos ni festivos
    5. Después de descanso requiere nuevo seed
    """
    
    # Cache de parámetros por fecha
    _parametros_cache = {}
    
    @classmethod
    def obtener_hora_inicio_nocturno(cls, fecha):
        """
        Obtiene la hora de inicio de jornada nocturna desde BD.
        
        ANTES: Hardcodeado a 19:00
        AHORA: Lee de ParametroNormativo.obtener_vigente(fecha)
        """
        from .models_normativo import ParametroNormativo
        
        if fecha not in cls._parametros_cache:
            parametros = ParametroNormativo.obtener_vigente(fecha)
            if parametros:
                cls._parametros_cache[fecha] = parametros.hora_inicio_nocturno
            else:
                # Fallback: usar 21:00 como default pre-reforma
                cls._parametros_cache[fecha] = time(21, 0)
        
        return cls._parametros_cache[fecha]
    
    # Configuración de rangos por turno y tipo de día
    # Mar=1, Mié=2, Jue=3, Vie=4 son "semana"
    # Sáb=5, Dom=6, Lun=0 son "fin_semana"
    # Configuración de rangos por turno y tipo de día
    # Mar=1, Mié=2, Jue=3, Vie=4 son "semana"
    # Sáb=5, Dom=6, Lun=0 son "fin_semana"
    RANGOS_TURNO = {
        'M': {
            'semana': (time(7, 0), time(14, 0)),      # 7h (Mar-Vie)
            'fin_semana': (time(6, 0), time(14, 0)),  # 8h (Lun/Sáb/Dom)
        },
        'T': {
            'semana': (time(16, 0), time(23, 0)),     # 7h (Mar-Vie)
            'fin_semana': (time(14, 0), time(22, 0)), # 8h (Lun/Sáb/Dom)
        },
        'A': {
            'semana': (time(13, 0), time(21, 0)),     # 8h (Lun-Vie)
            'fin_semana': None,  # No trabaja (Sáb/Dom/Festivos)
        },
        'N_W1': {
             # Primer Miércoles del bloque N: 11:00 pm a 11:59 pm (1h)
            'semana': (time(23, 0), time(23, 59)), 
            'fin_semana': (time(23, 0), time(23, 59)),
        },
        'N_W2': {
            # Último Miércoles (Salida): 12:00 am a 06:00 am (6h)
            'semana': (time(0, 0), time(6, 0)),
            'fin_semana': (time(0, 0), time(6, 0)),
        },
        'D': {
            'semana': None,
            'fin_semana': None,
        }
    }
    
    @classmethod
    def es_fin_semana(cls, fecha):
        """Sáb=5, Dom=6, Lun=0 son considerados fin de semana para horarios"""
        return fecha.weekday() in [0, 5, 6]
    
    @classmethod
    def es_festivo(cls, fecha):
        """Verifica si la fecha es festivo en Colombia"""
        import holidays
        co_holidays = holidays.CO()
        return fecha in co_holidays
    
    @classmethod
    def obtener_festivos_rango(cls, fecha_inicio, fecha_fin):
        """Obtiene lista de festivos en un rango de fechas"""
        import holidays
        co_holidays = holidays.CO(years=[fecha_inicio.year, fecha_fin.year])
        festivos = set()
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            if fecha_actual in co_holidays:
                festivos.add(fecha_actual)
            fecha_actual += timedelta(days=1)
        return festivos
    
    @classmethod
    def obtener_rangos_horarios(cls, turno, fecha, festivos=None, context_vecindad=None):
        """
        Obtiene los segmentos horarios reales para un turno en una fecha.
        
        Args:
            turno: 'M', 'T', 'N', 'A', 'D'
            fecha: date
            festivos: set de fechas festivas
            context_vecindad: dict { 'prev': 'N', 'today': 'N', 'next': 'N' }
        
        Returns:
            Lista de segmentos: [{'inicio': time, 'fin': time, 'cruza_medianoche': bool}]
        """
        if festivos is None:
            festivos = set()
        
        es_finde = cls.es_fin_semana(fecha)
        es_fest = fecha in festivos or cls.es_festivo(fecha)
        
        # Turno D (Descanso)
        if turno == 'D':
            return []
        
        # Turno A (Apoyo) - No trabaja sábados, domingos ni festivos (Lunes SI trabaja)
        if turno == 'A':
            # Solo Sáb(5) y Dom(6) son descanso, Lunes(0) es laboral para A
            es_sab_dom = fecha.weekday() in [5, 6]
            if es_sab_dom or es_fest:
                return []
            rango = cls.RANGOS_TURNO['A']['semana']
            return [{'inicio': rango[0], 'fin': rango[1], 'cruza_medianoche': False}]
        
        # Turno M (Mañana)
        if turno == 'M':
            tipo_dia = 'fin_semana' if es_finde else 'semana'
            rango = cls.RANGOS_TURNO['M'][tipo_dia]
            return [{'inicio': rango[0], 'fin': rango[1], 'cruza_medianoche': False}]
        
        # Turno T (Tarde)
        if turno == 'T':
            tipo_dia = 'fin_semana' if es_finde else 'semana'
            rango = cls.RANGOS_TURNO['T'][tipo_dia]
            return [{'inicio': rango[0], 'fin': rango[1], 'cruza_medianoche': False}]
            
        # N_W1 (Primer Miércoles) - Estático
        if turno == 'N_W1':
            rango = cls.RANGOS_TURNO['N_W1']['semana']
            return [{'inicio': rango[0], 'fin': rango[1], 'cruza_medianoche': False, 'es_noche': True}]

        # N_W2 (Salida Noche) - Estático (Madrugada pura)
        if turno == 'N_W2':
            rango = cls.RANGOS_TURNO['N_W2']['semana']
            return [{'inicio': rango[0], 'fin': rango[1], 'cruza_medianoche': False, 'es_madrugada': True}]
        
        # Turno N (Noche) - Lógica de VECINDAD
        if turno == 'N':
            # Si no hay contexto, asumimos N estándar (fallback riesgoso pero necesario)
            if context_vecindad is None:
                context_vecindad = {'prev': 'N', 'today': 'N', 'next': 'N'}
            
            return cls._obtener_rangos_turno_n_vecindad(fecha, context_vecindad)
        
        return []
    
    @classmethod
    def _obtener_rangos_turno_n_vecindad(cls, fecha, context):
        """
        Lógica V5 para turno N basada en VECINDAD.
        
        Reglas:
        1. madrugada (6h) SOLO si prev == 'N' y today == 'N'
        2. noche SOLO si today == 'N' y next == 'N'
           - Mar-Vie: 1h (23:00-00:00)
           - Sáb-Dom-Lun: 2h (22:00-00:00)
        """
        segmentos = []
        
        prev_is_N = context.get('prev') == 'N'
        today_is_N = context.get('today') == 'N'
        next_is_N = context.get('next') == 'N'
        
        # Si hoy NO es N, retorno vacío (regla de oro)
        if not today_is_N:
            return []
            
        # 1. Segmento Madrugada (00:00 - 06:00)
        # Solo si ayer también fue N (continuidad)
        if prev_is_N:
             segmentos.append({
                'inicio': time(0, 0),
                'fin': time(6, 0),
                'cruza_medianoche': False,
                'es_madrugada': True
            })
            
        # 2. Segmento Noche (inicia hoy)
        # Solo si mañana también será N (continuidad)
        if next_is_N:
            es_finde_o_lun = fecha.weekday() in [0, 5, 6] # Lun, Sáb, Dom
            
            if es_finde_o_lun: # 22:00 - 00:00 (2h)
                segmentos.append({
                    'inicio': time(22, 0),
                    'fin': time(23, 59), # Representa 24:00
                    'cruza_medianoche': False,
                    'es_noche': True
                })
            else: # Mar-Vie: 23:00 - 00:00 (1h)
                segmentos.append({
                    'inicio': time(23, 0),
                    'fin': time(23, 59), # Representa 24:00
                    'cruza_medianoche': False,
                    'es_noche': True
                })
        
        return segmentos
    
    @classmethod
    def calcular_horas_segmento(cls, segmento):
        """Calcula las horas de un segmento horario"""
        inicio = segmento['inicio']
        fin = segmento['fin']
        
        # Convertir a minutos desde medianoche
        mins_inicio = inicio.hour * 60 + inicio.minute
        mins_fin = fin.hour * 60 + fin.minute
        
        # Si termina a las 23:59, considerarlo como 24:00 (0 del día siguiente)
        if mins_fin == 23 * 60 + 59:
            mins_fin = 24 * 60
        
        if mins_fin > mins_inicio:
            return Decimal(str((mins_fin - mins_inicio) / 60))
        else:
            # Cruza medianoche
            return Decimal(str((24 * 60 - mins_inicio + mins_fin) / 60))
    
    @classmethod
    def calcular_recargos_segmento(cls, segmento, es_domingo, es_festivo):
        """
        Calcula HOD, RNO, RDF, RNF para UN segmento horario.
        RNO inicia a las 19:00.
        
        Returns:
            dict con 'hod', 'rno', 'rdf', 'rnf'
        """
        inicio = segmento['inicio']
        fin = segmento['fin']
        
        # Convertir a minutos
        mins_inicio = inicio.hour * 60 + inicio.minute
        mins_fin = fin.hour * 60 + fin.minute
        mins_nocturno = 19 * 60  # 19:00
        
        # Ajustar 23:59 a 24:00
        if mins_fin == 23 * 60 + 59:
            mins_fin = 24 * 60
        
        # Calcular horas diurnas y nocturnas
        if mins_fin <= mins_nocturno:
            # Todo antes de las 19:00
            horas_diurnas = Decimal(str((mins_fin - mins_inicio) / 60))
            horas_nocturnas = Decimal('0')
        elif mins_inicio >= mins_nocturno:
            # Todo después de las 19:00
            horas_diurnas = Decimal('0')
            horas_nocturnas = Decimal(str((mins_fin - mins_inicio) / 60))
        else:
            # Parte diurna y parte nocturna
            horas_diurnas = Decimal(str((mins_nocturno - mins_inicio) / 60))
            horas_nocturnas = Decimal(str((mins_fin - mins_nocturno) / 60))
        
        # Asignar a categorías legales
        if es_festivo or es_domingo:
            return {
                'hod': Decimal('0'),
                'rno': Decimal('0'),
                'rdf': horas_diurnas,
                'rnf': horas_nocturnas
            }
        else:
            return {
                'hod': horas_diurnas,
                'rno': horas_nocturnas,
                'rdf': Decimal('0'),
                'rnf': Decimal('0')
            }
    
    @classmethod
    def calcular_recargos_fecha(cls, turno, fecha, festivos=None, context_vecindad=None):
        """
        Calcula todos los recargos para una fecha específica.
        
        Returns:
            dict con 'horas_trabajadas', 'hod', 'rno', 'rdf', 'rnf', 'segmentos'
        """
        if festivos is None:
            festivos = set()
        
        es_domingo = fecha.weekday() == 6
        es_fest = fecha in festivos or cls.es_festivo(fecha)
        
        segmentos = cls.obtener_rangos_horarios(turno, fecha, festivos, context_vecindad)
        
        totales = {
            'horas_trabajadas': Decimal('0'),
            'hod': Decimal('0'),
            'rno': Decimal('0'),
            'rdf': Decimal('0'),
            'rnf': Decimal('0'),
            'segmentos': segmentos
        }
        
        for seg in segmentos:
            horas_seg = cls.calcular_horas_segmento(seg)
            recargos_seg = cls.calcular_recargos_segmento(seg, es_domingo, es_fest)
            
            totales['horas_trabajadas'] += horas_seg
            totales['hod'] += recargos_seg['hod']
            totales['rno'] += recargos_seg['rno']
            totales['rdf'] += recargos_seg['rdf']
            totales['rnf'] += recargos_seg['rnf']
        
        return totales
    
    @classmethod
    def obtener_posicion_en_bloque_n(cls, fecha, seed_fecha, seed_turno):
        """
        Calcula la posición del operador en el bloque N (0-7).
        
        El ciclo completo es: T(7) + N(8) + D(6) + M(7) = 28 días
        El bloque N va del día 7 al 14 del ciclo.
        
        Returns:
            0-7 si está en turno N, None si no está en N
        """
        # Offset según turno inicial del seed
        offset_turno = {'T': 0, 'N': 7, 'D': 15, 'M': 21, 'A': 0}
        
        # Si el seed es turno A (fijo), no aplica el ciclo N
        if seed_turno == 'A':
            return None
        
        dias_desde_seed = (fecha - seed_fecha).days
        pos_en_ciclo = (dias_desde_seed + offset_turno.get(seed_turno, 0)) % 28
        
        # El bloque N ocupa posiciones 7-14 (8 días)
        if 7 <= pos_en_ciclo <= 14:
            return pos_en_ciclo - 7  # 0 = primer día, 7 = último día
        
        return None
    
    @classmethod
    def generar_turnos_operador_v4(cls, operador, fecha_inicio, fecha_fin):
        """
        Genera turnos con rangos horarios reales y recargos legales.
        
        Returns:
            Lista de RegistroTurno listos para guardar
        """
        from apps.horas_extras.models import TipoTurno, RegistroTurno, PatronOperador
        
        # Obtener tipos de turno
        tipos_turno = {}
        for codigo in ['T', 'N', 'D', 'M', 'A']:
            try:
                tipos_turno[codigo] = TipoTurno.objects.get(codigo=codigo)
            except TipoTurno.DoesNotExist:
                pass
        
        # Verificar que existe al menos un seed
        if not PatronOperador.objects.filter(operador=operador).exists():
            raise ValueError(
                f"No existe PatronOperador para {operador.get_full_name()}. "
                f"Use: set_patron_operador --operador {operador.username} --fecha YYYY-MM-DD --turno T/N/D/M/A"
            )
        
        # Obtener festivos del rango
        festivos = cls.obtener_festivos_rango(fecha_inicio, fecha_fin)
        
        turnos_generados = []
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            # Obtener seed vigente para esta fecha
            seed = PatronOperador.obtener_seed_vigente(operador, fecha_actual)
            
            if not seed:
                # Sin seed para esta fecha, saltar
                fecha_actual += timedelta(days=1)
                continue
            
            # Calcular turno del día
            turno_codigo = seed.calcular_turno_fecha(fecha_actual)
            
            if turno_codigo not in tipos_turno:
                fecha_actual += timedelta(days=1)
                continue
            
            tipo_turno = tipos_turno[turno_codigo]
            
            # Determinar contexto de vecindad para turno N
            context_vecindad = None
            if turno_codigo == 'N':
                # Obtener turno anterior y siguiente usando el MISMO seed (asumimos continuidad de patrón)
                # En un caso ideal, deberíamos buscar si hay OTRO seed que aplique, pero para generación
                # masiva basada en un patrón, usar el mismo seed para +/- 1 día es lo correcto.
                turno_ayer = seed.calcular_turno_fecha(fecha_actual - timedelta(days=1))
                turno_manana = seed.calcular_turno_fecha(fecha_actual + timedelta(days=1))
                
                context_vecindad = {
                    'prev': turno_ayer,
                    'today': 'N',
                    'next': turno_manana
                }

            # Calcular recargos con rangos reales
            recargos = cls.calcular_recargos_fecha(
                turno_codigo, 
                fecha_actual, 
                festivos,
                context_vecindad
            )
            
            # Determinar hora inicio/fin para el registro
            hora_inicio = None
            hora_fin = None
            if recargos['segmentos']:
                hora_inicio = recargos['segmentos'][0]['inicio']
                hora_fin = recargos['segmentos'][-1]['fin']
            
            # Crear registro
            registro = RegistroTurno(
                operador=operador,
                tipo_turno=tipo_turno,
                fecha=fecha_actual,
                estado='programado',
                hora_inicio_real=hora_inicio,
                hora_fin_real=hora_fin,
                horas_trabajadas=recargos['horas_trabajadas']
            )
            
            turnos_generados.append(registro)
            fecha_actual += timedelta(days=1)
        
        return turnos_generados
    
    @classmethod
    def guardar_turnos(cls, turnos):
        """Guarda lista de turnos en la base de datos"""
        for turno in turnos:
            turno.save()
        return len(turnos)
