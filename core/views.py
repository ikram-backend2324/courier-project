from django.shortcuts import render, redirect
from routes.models import Route, Courier, DeliveryPoint

def home(request):
    total_routes = Route.objects.count()
    total_couriers = Courier.objects.filter(is_active=True).count()
    total_deliveries = DeliveryPoint.objects.count()
    completed_routes = Route.objects.filter(status='completed').count()
    recent_routes = Route.objects.select_related('courier').order_by('-created_at')[:5]
    return render(request, 'core/home.html', {
        'total_routes': total_routes,
        'total_couriers': total_couriers,
        'total_deliveries': total_deliveries,
        'completed_routes': completed_routes,
        'recent_routes': recent_routes,
    })

def set_language(request):
    lang = request.POST.get('language', 'en')
    if lang in ['en', 'ru', 'uz']:
        request.session['language'] = lang
    next_url = request.POST.get('next', '/')
    return redirect(next_url)
