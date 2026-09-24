# -- VISTAS DEL CATÁLOGO DE BENEFICIOS Y MEMBRESÍAS --
from django.shortcuts import render
from .models import Benefit

def benefits_list_view(request):
    # -- LISTADO PÚBLICO DE BENEFICIOS PARA PROFESIONALES --
    benefits = Benefit.objects.filter(is_active=True)
    return render(request, 'benefits/lista_beneficios.html', {'benefits': benefits})
