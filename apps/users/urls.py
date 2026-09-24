from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='services:marketplace'), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/pro/', views.pro_dashboard_view, name='pro_dashboard'),
    path('dashboard/org/', views.org_dashboard_view, name='org_dashboard'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('pro/<slug:slug>/', views.public_pro_profile_view, name='public_pro_profile'),
]
