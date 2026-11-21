from django.shortcuts import render
from .models import Benefit

def benefits_list_view(request):
    benefits = Benefit.objects.filter(is_active=True)
    return render(request, 'benefits/lista_beneficios.html', {'benefits': benefits})
