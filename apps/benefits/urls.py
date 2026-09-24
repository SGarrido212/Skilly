from django.urls import path
from . import views

app_name = 'benefits'

urlpatterns = [
    path('', views.benefits_list_view, name='list'),
]
