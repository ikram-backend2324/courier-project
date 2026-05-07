from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    path('', views.route_list, name='list'),
    path('create/', views.route_create, name='create'),
    path('<int:pk>/', views.route_detail, name='detail'),
    path('<int:pk>/plan-ai/', views.plan_with_ai, name='plan_ai'),
    path('api/couriers/', views.get_couriers, name='api_couriers'),
    path('api/courier/<int:pk>/location/', views.get_courier_location, name='api_courier_location'),
]
