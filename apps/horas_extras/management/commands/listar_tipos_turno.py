# -*- coding: utf-8 -*-
"""
Django management command to list all TipoTurno in the database.
Usage: python manage.py listar_tipos_turno
"""

from django.core.management.base import BaseCommand
from apps.horas_extras.models import TipoTurno


class Command(BaseCommand):
    help = 'Lista todos los tipos de turno en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("TIPOS DE TURNO EN LA BASE DE DATOS")
        self.stdout.write("=" * 60)
        
        tipos = TipoTurno.objects.all().order_by('codigo')
        
        if not tipos:
            self.stdout.write(self.style.ERROR("No hay tipos de turno en la base de datos"))
            return
        
        self.stdout.write("")
        self.stdout.write("%-20s %-30s %s" % ("CODIGO", "DESCRIPCION", "NOCTURNO"))
        self.stdout.write("-" * 60)
        
        for tipo in tipos:
            nocturno = "SI" if tipo.es_nocturno else "NO"
            self.stdout.write("%-20s %-30s %s" % (tipo.codigo, tipo.descripcion, nocturno))
        
        self.stdout.write("-" * 60)
        self.stdout.write("")
        self.stdout.write("Total: %s tipos de turno" % tipos.count())
