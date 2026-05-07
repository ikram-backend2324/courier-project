from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from routes.models import Route, Courier, DeliveryPoint


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, 'invalid_credentials')

    return render(request, 'core/login.html', {'next': request.GET.get('next', '/')})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('core:login')


@login_required(login_url='/login/')
def home(request):
    user = request.user

    # Admins/staff see all data
    if user.is_staff or user.is_superuser:
        total_routes = Route.objects.count()
        total_couriers = Courier.objects.filter(is_active=True).count()
        total_deliveries = DeliveryPoint.objects.count()
        completed_routes = Route.objects.filter(status='completed').count()
        recent_routes = Route.objects.select_related('courier').order_by('-created_at')[:5]
        is_admin = True
    else:
        # Courier sees only their own data
        try:
            courier = Courier.objects.get(user=user)
            total_routes = Route.objects.filter(courier=courier).count()
            total_couriers = 1
            total_deliveries = DeliveryPoint.objects.filter(route__courier=courier).count()
            completed_routes = Route.objects.filter(courier=courier, status='completed').count()
            recent_routes = Route.objects.filter(courier=courier).order_by('-created_at')[:5]
        except Courier.DoesNotExist:
            total_routes = 0
            total_couriers = 0
            total_deliveries = 0
            completed_routes = 0
            recent_routes = []
        is_admin = False

    return render(request, 'core/home.html', {
        'total_routes': total_routes,
        'total_couriers': total_couriers,
        'total_deliveries': total_deliveries,
        'completed_routes': completed_routes,
        'recent_routes': recent_routes,
        'is_admin': is_admin,
    })


def set_language(request):
    lang = request.POST.get('language', 'en')
    if lang in ['en', 'ru', 'uz']:
        request.session['language'] = lang
    next_url = request.POST.get('next', '/')
    return redirect(next_url)
