from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def home(request):
    """Vista de inicio del proyecto CotizaBelleza"""
    return HttpResponse("<h1>¡Bienvenido a CotizaBelleza!</h1><p>El proyecto Django está funcionando correctamente.</p>")
