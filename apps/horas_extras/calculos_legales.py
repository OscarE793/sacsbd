# apps/horas_extras/calculos_legales.py
"""
Motor de cálculo legal para nómina colombiana (SACSBD).
Refactorizado para usar ParametroNormativo de BD.

NO genera horas extras.
Clasifica en: HOD, RNO, RDF, RNF.
"""

import datetime
from decimal import Decimal
import holidays
from django.utils import timezone

from .models_normativo import ParametroNormativo


class CalculadoraLegal:
    """
    Motor de cálculo estricto para nómina colombiana.
    
    IMPORTANTE: Ahora usa parámetros de BD en lugar de valores hardcodeados.
    Para cambios de ley, crear nuevo registro en ParametroNormativo.
    """

    def __init__(self):
        # Cache de festivos de Colombia
        self.co_holidays = holidays.CO()
        # Cache de parámetros por fecha
        self._parametros_cache = {}

    def _obtener_parametros(self, fecha):
        """
        Obtiene parámetros normativos vigentes para una fecha.
        Usa cache para evitar consultas repetidas.
        """
        if fecha not in self._parametros_cache:
            parametros = ParametroNormativo.obtener_vigente(fecha)
            if not parametros:
                # Fallback: crear instancia con defaults
                parametros = ParametroNormativo()
            self._parametros_cache[fecha] = parametros
        return self._parametros_cache[fecha]

    def es_festivo(self, fecha):
        """Verifica si una fecha es festivo en Colombia"""
        return fecha in self.co_holidays

    def obtener_inicio_nocturno(self, fecha):
        """
        Determina la hora de inicio de la franja nocturna según parámetros de BD.
        
        ANTES: Hardcodeado (21 antes de 25/12/2025, 19 después)
        AHORA: Lee de ParametroNormativo.hora_inicio_nocturno
        """
        parametros = self._obtener_parametros(fecha)
        return parametros.hora_inicio_nocturno.hour

    def obtener_fin_nocturno(self, fecha):
        """Obtiene hora fin de jornada nocturna desde BD."""
        parametros = self._obtener_parametros(fecha)
        return parametros.hora_fin_nocturno.hour

    def es_hora_nocturna(self, fecha, hora):
        """
        Determina si una hora específica es nocturna según parámetros vigentes.
        
        Args:
            fecha: date para consultar parámetros vigentes
            hora: int (0-23)
            
        Returns:
            bool: True si es nocturna
        """
        parametros = self._obtener_parametros(fecha)
        return parametros.es_hora_nocturna(hora)

    def calcular_horas_turno(self, turno):
        """
        Calcula el desglose de horas para un turno usando los intervalos REALES.
        Usa hora_inicio_real y hora_fin_real del objeto turno.
        Retorna: { fecha: {HOD, RNO, RDF, RNF, TOTAL} }
        
        Reglas:
        - Divide las horas en el día calendario donde realmente se trabajan
        - Clasifica cada hora según si es festivo/domingo (RNF) o no (RNO)
        - Para turno nocturno (N), TODAS las horas son nocturnas (RNO o RNF)
        
        REGLA ESPECIAL PARA TURNO N:
        - horas_trabajadas es la ÚNICA fuente de verdad
        - NO hacer split por medianoche
        - El último miércoles N (6h) SIEMPRE pertenece al miércoles
        """
        resultado = {}
        fecha_turno = turno.fecha
        
        # Obtener código y tipo de turno
        codigo_turno = None
        tipo_turno = None
        if hasattr(turno, 'tipo_turno') and turno.tipo_turno:
            codigo_turno = turno.tipo_turno.codigo
            tipo_turno = turno.tipo_turno
        
        # ========== TURNO DESCANSO (D) = 0 HORAS ==========
        if codigo_turno == 'D':
            resultado[fecha_turno] = {
                'HOD': Decimal('0.0'),
                'RNO': Decimal('0.0'),
                'RDF': Decimal('0.0'),
                'RNF': Decimal('0.0'),
                'TOTAL': Decimal('0.0')
            }
            return resultado
        
        # ========== OBTENER HORAS CORRECTAS PARA EL DÍA ==========
        # Prioridad: 1) horas del TipoTurno para el día específico, 2) horas_trabajadas del registro
        horas = Decimal('0.0')
        if tipo_turno:
            _, _, horas_dia = tipo_turno.get_horario_por_dia(fecha_turno)
            horas = horas_dia or Decimal('0.0')
        
        # Fallback a horas_trabajadas si no hay configuración por día
        if horas == Decimal('0.0') and hasattr(turno, 'horas_trabajadas') and turno.horas_trabajadas:
            horas = turno.horas_trabajadas
        
        # ========== REGLA ESPECIAL PARA TURNOS NOCTURNOS (N, N_W1, N_W2) ==========
        if codigo_turno in ['N', 'N_W1', 'N_W2']:
            # En V5, los turnos N ya deben venir con sus horas reales calculadas por el Generador
            # Si tienen horas > 0, respetamos la distribución (o todo nocturno si es simplificado)
            if horas > 0:
                resultado[fecha_turno] = {
                    'HOD': Decimal('0.0'),
                    'RNO': Decimal('0.0'),
                    'RDF': Decimal('0.0'),
                    'RNF': Decimal('0.0'),
                    'TOTAL': horas
                }
                
                # Clasificar todas las horas N como nocturnas
                es_dia_festivo = self.es_festivo(fecha_turno) or (fecha_turno.weekday() == 6)
                
                if es_dia_festivo:
                    resultado[fecha_turno]['RNF'] = horas
                else:
                    resultado[fecha_turno]['RNO'] = horas
            
            return resultado
        
        # ========== LÓGICA PARA TURNOS DIURNOS (M, T, A) ==========
        # Si no hay horas configuradas, retornar 0 explícito
        if horas <= 0:
            resultado[fecha_turno] = {
                'HOD': Decimal('0.0'),
                'RNO': Decimal('0.0'),
                'RDF': Decimal('0.0'),
                'RNF': Decimal('0.0'),
                'TOTAL': Decimal('0.0')
            }
            return resultado
        
        # Determinar si es festivo o domingo
        es_day_festivo = self.es_festivo(fecha_turno) or (fecha_turno.weekday() == 6)
        
        # Inicializar resultado para la fecha
        # ERROR FIX: Inicializar en 0, no en 'horas', porque luego se suma en el bucle
        resultado[fecha_turno] = {
            'HOD': Decimal('0.0'),
            'RNO': Decimal('0.0'),
            'RDF': Decimal('0.0'),
            'RNF': Decimal('0.0'),
            'TOTAL': Decimal('0.0')
        }
        
        # Para turnos diurnos, clasificar basándose en si hay hora_inicio_real/hora_fin_real
        hora_inicio = getattr(turno, 'hora_inicio_real', None)
        hora_fin = getattr(turno, 'hora_fin_real', None)
        
        if hora_inicio and hora_fin:
            # Si hay horarios reales, hacer cálculo hora por hora
            dt_inicio = datetime.datetime.combine(fecha_turno, hora_inicio)
            dt_fin = datetime.datetime.combine(fecha_turno, hora_fin)
            
            # Si hora_fin < hora_inicio, el turno cruza medianoche
            if hora_fin <= hora_inicio:
                dt_fin += datetime.timedelta(days=1)
            
            # Iterar hora por hora
            dt_actual = dt_inicio
            horas_contadas = Decimal('0.0')
            
            while dt_actual < dt_fin: # Eliminado 'and horas_contadas < horas' para ser exactos con el rango
                fecha_actual = dt_actual.date()
                hora_actual = dt_actual.hour
                
                # Inicializar si no existe (por si cruza medianoche a otro día)
                if fecha_actual not in resultado:
                    resultado[fecha_actual] = {
                        'HOD': Decimal('0.0'),
                        'RNO': Decimal('0.0'),
                        'RDF': Decimal('0.0'),
                        'RNF': Decimal('0.0'),
                        'TOTAL': Decimal('0.0')
                    }
                
                # Determinar si es hora nocturna
                es_hora_nocturna = self.es_hora_nocturna(fecha_actual, hora_actual)
                es_dia_fest = self.es_festivo(fecha_actual) or (fecha_actual.weekday() == 6)
                
                # Clasificar la hora
                if es_dia_fest:
                    key = 'RNF' if es_hora_nocturna else 'RDF'
                else:
                    key = 'RNO' if es_hora_nocturna else 'HOD'
                
                resultado[fecha_actual][key] += Decimal('1.0')
                resultado[fecha_actual]['TOTAL'] += Decimal('1.0')
                horas_contadas += Decimal('1.0')
                
                dt_actual += datetime.timedelta(hours=1)
        else:
            # Sin horarios reales, usar clasificación simple basada en tipo de turno
            resultado[fecha_turno]['TOTAL'] = horas
            if es_day_festivo:
                # En festivo: RDF (diurno festivo)
                resultado[fecha_turno]['RDF'] = horas
            else:
                # Día normal: HOD (ordinario diurno)
                resultado[fecha_turno]['HOD'] = horas
        
        return resultado

    def calcular_horas(self, fecha_turno, codigo_turno):
        """
        Método legacy para compatibilidad.
        Calcula horas usando horarios teóricos cuando no hay turno real.
        Retorna: { fecha: {HOD, RNO, RDF, RNF, TOTAL} }
        """
        resultado = {}
        
        # Normalizar código de turno
        codigo = codigo_turno.upper().strip()
        
        # ========== DESCANSO = 0 HORAS ==========
        if codigo in ['D', 'DESCANSO']:
            resultado[fecha_turno] = {
                'HOD': Decimal('0.0'),
                'RNO': Decimal('0.0'),
                'RDF': Decimal('0.0'),
                'RNF': Decimal('0.0'),
                'TOTAL': Decimal('0.0')
            }
            return resultado
        
        # ========== N_W1 = 1 hora nocturna, N_W2 = 6 horas nocturnas ==========
        if codigo in ['N_W1', 'N_W2']:
            horas = Decimal('1.0') if codigo == 'N_W1' else Decimal('6.0')
            resultado[fecha_turno] = {
                'HOD': Decimal('0.0'),
                'RNO': Decimal('0.0'),
                'RDF': Decimal('0.0'),
                'RNF': Decimal('0.0'),
                'TOTAL': horas
            }
            es_dia_festivo = self.es_festivo(fecha_turno) or (fecha_turno.weekday() == 6)
            resultado[fecha_turno]['RNF' if es_dia_festivo else 'RNO'] = horas
            return resultado
        
        # Definir horarios teóricos según el tipo de turno
        hora_inicio = 0
        hora_fin = 0
        cruza_dia = False
        
        if codigo in ['1-M', 'MAÑANA', 'M', 'MANANA', 'TURNO 1-M']:
            hora_inicio = 6
            hora_fin = 14
        elif codigo in ['2-T', 'TARDE', 'T', 'TURNO 2-T']:
            hora_inicio = 14
            hora_fin = 22
        elif codigo in ['3-N', 'NOCHE', 'N', 'TURNO 3-N']:
            hora_inicio = 23
            hora_fin = 6
            cruza_dia = True
        elif codigo in ['APOYO', 'A', 'APOYO-A']:
            hora_inicio = 13
            hora_fin = 21
        else:
            return resultado  # Código desconocido
        
        # Calcular duración
        if cruza_dia:
            duracion = (24 - hora_inicio) + hora_fin
        else:
            duracion = hora_fin - hora_inicio
        
        # Ajuste de duración para Martes-Viernes (7 horas) 
        dia_semana = fecha_turno.weekday()
        if dia_semana in [1, 2, 3, 4]:  # Martes a Viernes
            if cruza_dia:
                hora_inicio = 23
            else:
                duracion = 7
        
        # Iterar hora por hora
        hora_actual = hora_inicio
        fecha_actual = fecha_turno
        horas_procesadas = 0
        
        while horas_procesadas < duracion:
            # Inicializar acumulador para esta fecha
            if fecha_actual not in resultado:
                resultado[fecha_actual] = {
                    'HOD': Decimal('0.0'),
                    'RNO': Decimal('0.0'),
                    'RDF': Decimal('0.0'),
                    'RNF': Decimal('0.0'),
                    'TOTAL': Decimal('0.0')
                }
            
            # Determinar si es hora nocturna usando parámetros de BD
            es_hora_nocturna = self.es_hora_nocturna(fecha_actual, hora_actual)
            
            # Determinar si es festivo o domingo
            es_dia_festivo = self.es_festivo(fecha_actual) or (fecha_actual.weekday() == 6)
            
            # Clasificar la hora
            if es_dia_festivo:
                key = 'RNF' if es_hora_nocturna else 'RDF'
            else:
                key = 'RNO' if es_hora_nocturna else 'HOD'
            
            resultado[fecha_actual][key] += Decimal('1.0')
            resultado[fecha_actual]['TOTAL'] += Decimal('1.0')
            
            # Avanzar hora
            hora_actual += 1
            horas_procesadas += 1
            
            # Cruce de medianoche
            if hora_actual >= 24:
                hora_actual = 0
                fecha_actual = fecha_actual + datetime.timedelta(days=1)
        
        return resultado
    
    def obtener_info_parametros(self, fecha):
        """
        Retorna información de los parámetros vigentes para mostrar en reportes.
        
        Returns:
            dict con información formateada
        """
        parametros = self._obtener_parametros(fecha)
        return {
            'vigencia_desde': parametros.vigencia_desde,
            'hora_inicio_nocturno': parametros.hora_inicio_nocturno.strftime('%H:%M'),
            'hora_fin_nocturno': parametros.hora_fin_nocturno.strftime('%H:%M'),
            'recargo_nocturno': f"{int(parametros.recargo_nocturno * 100)}%",
            'recargo_dominical': f"{int(parametros.recargo_dominical_festivo * 100)}%",
            'jornada_semanal': parametros.jornada_semanal_max,
            'descripcion': parametros.descripcion
        }
