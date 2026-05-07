from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('set-language/', views.set_language, name='set_language'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
