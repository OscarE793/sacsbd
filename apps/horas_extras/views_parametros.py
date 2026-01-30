# apps/horas_extras/views_parametros.py
"""
Vistas para gestionar Parámetros Normativos desde la interfaz SACSBD.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from datetime import date

from .models_normativo import ParametroNormativo, PoliticaEmpresa
from .forms_parametros import ParametroNormativoForm, PoliticaEmpresaForm


def es_administrador(user):
    """Verifica que el usuario sea administrador o staff"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(es_administrador)
def listar_parametros_normativos(request):
    """
    Lista todos los parámetros normativos del sistema.
    Vista principal de configuración.
    """
    parametros = ParametroNormativo.objects.all().order_by('-vigencia_desde')
    
    # Identificar cuál está vigente hoy
    hoy = date.today()
    parametro_vigente = ParametroNormativo.obtener_vigente(hoy)
    
    context = {
        'parametros': parametros,
        'parametro_vigente': parametro_vigente,
        'hoy': hoy,
        'titulo': 'Parámetros Normativos',
        'breadcrumb': [
            {'titulo': 'Inicio', 'url': '/'},
            {'titulo': 'Horas Extras', 'url': '/horas-extras/'},
            {'titulo': 'Parámetros Normativos', 'url': None}
        ]
    }
    
    return render(request, 'horas_extras/parametros/listar.html', context)


@login_required
@user_passes_test(es_administrador)
def crear_parametro_normativo(request):
    """Crea un nuevo parámetro normativo"""
    
    if request.method == 'POST':
        form = ParametroNormativoForm(request.POST)
        if form.is_valid():
            parametro = form.save()
            messages.success(
                request,
                f'Parámetro normativo creado exitosamente. '
                f'Vigente desde: {parametro.vigencia_desde}'
            )
            return redirect('horas_extras:listar_parametros_normativos')
    else:
        form = ParametroNormativoForm()
    
    context = {
        'form': form,
        'titulo': 'Nuevo Parámetro Normativo',
        'accion': 'Crear',
        'breadcrumb': [
            {'titulo': 'Inicio', 'url': '/'},
            {'titulo': 'Horas Extras', 'url': '/horas-extras/'},
            {'titulo': 'Parámetros Normativos', 'url': 'horas_extras:listar_parametros_normativos'},
            {'titulo': 'Nuevo', 'url': None}
        ]
    }
    
    return render(request, 'horas_extras/parametros/formulario.html', context)


@login_required
@user_passes_test(es_administrador)
def editar_parametro_normativo(request, parametro_id):
    """Edita un parámetro normativo existente"""
    
    parametro = get_object_or_404(ParametroNormativo, id=parametro_id)
    
    if request.method == 'POST':
        form = ParametroNormativoForm(request.POST, instance=parametro)
        if form.is_valid():
            parametro = form.save()
            messages.success(
                request,
                f'Parámetro normativo actualizado exitosamente.'
            )
            return redirect('horas_extras:listar_parametros_normativos')
    else:
        form = ParametroNormativoForm(instance=parametro)
    
    context = {
        'form': form,
        'parametro': parametro,
        'titulo': 'Editar Parámetro Normativo',
        'accion': 'Actualizar',
        'breadcrumb': [
            {'titulo': 'Inicio', 'url': '/'},
            {'titulo': 'Horas Extras', 'url': '/horas-extras/'},
            {'titulo': 'Parámetros Normativos', 'url': 'horas_extras:listar_parametros_normativos'},
            {'titulo': 'Editar', 'url': None}
        ]
    }
    
    return render(request, 'horas_extras/parametros/formulario.html', context)


@login_required
@user_passes_test(es_administrador)
def ver_parametro_normativo(request, parametro_id):
    """Muestra detalle de un parámetro normativo"""
    
    parametro = get_object_or_404(ParametroNormativo, id=parametro_id)
    
    # Ver si es el vigente hoy
    hoy = date.today()
    es_vigente = (parametro.vigencia_desde <= hoy and 
                  (parametro.vigencia_hasta is None or parametro.vigencia_hasta >= hoy))
    
    context = {
        'parametro': parametro,
        'es_vigente': es_vigente,
        'hoy': hoy,
        'titulo': f'Parámetro Normativo - {parametro.vigencia_desde}',
        'breadcrumb': [
            {'titulo': 'Inicio', 'url': '/'},
            {'titulo': 'Horas Extras', 'url': '/horas-extras/'},
            {'titulo': 'Parámetros Normativos', 'url': 'horas_extras:listar_parametros_normativos'},
            {'titulo': 'Detalle', 'url': None}
        ]
    }
    
    return render(request, 'horas_extras/parametros/detalle.html', context)


@login_required
@user_passes_test(es_administrador)
def eliminar_parametro_normativo(request, parametro_id):
    """
    Elimina un parámetro normativo.
    ADVERTENCIA: Solo permitir si no hay turnos que lo usen.
    """
    
    parametro = get_object_or_404(ParametroNormativo, id=parametro_id)
    
    if request.method == 'POST':
        # Verificar si es el único parámetro
        if ParametroNormativo.objects.count() <= 1:
            messages.error(
                request,
                'No se puede eliminar el último parámetro normativo del sistema.'
            )
            return redirect('horas_extras:listar_parametros_normativos')
        
        # Verificar si es el vigente actual
        hoy = date.today()
        parametro_vigente = ParametroNormativo.obtener_vigente(hoy)
        if parametro == parametro_vigente:
            messages.warning(
                request,
                'ADVERTENCIA: Estás eliminando el parámetro normativo actualmente vigente. '
                'Esto puede afectar los cálculos de horas.'
            )
        
        descripcion = parametro.descripcion[:50] if parametro.descripcion else str(parametro.vigencia_desde)
        parametro.delete()
        
        messages.success(
            request,
            f'Parámetro normativo "{descripcion}" eliminado exitosamente.'
        )
        return redirect('horas_extras:listar_parametros_normativos')
    
    context = {
        'parametro': parametro,
        'titulo': 'Eliminar Parámetro Normativo',
        'breadcrumb': [
            {'titulo': 'Inicio', 'url': '/'},
            {'titulo': 'Horas Extras', 'url': '/horas-extras/'},
            {'titulo': 'Parámetros Normativos', 'url': 'horas_extras:listar_parametros_normativos'},
            {'titulo': 'Eliminar', 'url': None}
        ]
    }
    
    return render(request, 'horas_extras/parametros/confirmar_eliminar.html', context)
