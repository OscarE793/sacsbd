from django.shortcuts import render
from django.http import HttpResponse

def test_metronic(request):
    """Vista de prueba para verificar integración Metronic + SACS_BD"""
    return render(request, 'test_metronic.html')

def test_ping(request):
    """Vista simple para verificar que Django funciona"""
    return HttpResponse("🚀 Django + SACS_BD funcionando correctamente!")
