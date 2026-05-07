import json
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Courier, Route, DeliveryPoint


def route_list(request):
    routes = Route.objects.select_related('courier').all()
    couriers = Courier.objects.filter(is_active=True)
    return render(request, 'routes/list.html', {'routes': routes, 'couriers': couriers})


def route_create(request):
    couriers = Courier.objects.filter(is_active=True)
    if request.method == 'POST':
        courier_id = request.POST.get('courier')
        title = request.POST.get('title')
        notes = request.POST.get('notes', '')
        courier_start_lat = request.POST.get('courier_start_lat')
        courier_start_lng = request.POST.get('courier_start_lng')
        courier_start_address = request.POST.get('courier_start_address', '')
        language = request.session.get('language', 'en')

        courier = get_object_or_404(Courier, id=courier_id)
        route = Route.objects.create(
            courier=courier,
            title=title,
            notes=notes,
            courier_start_lat=float(courier_start_lat) if courier_start_lat else None,
            courier_start_lng=float(courier_start_lng) if courier_start_lng else None,
            courier_start_address=courier_start_address,
            language=language,
        )

        # Save delivery points
        addresses = request.POST.getlist('address[]')
        lats = request.POST.getlist('lat[]')
        lngs = request.POST.getlist('lng[]')
        order_numbers = request.POST.getlist('order_number[]')
        recipient_names = request.POST.getlist('recipient_name[]')
        recipient_phones = request.POST.getlist('recipient_phone[]')
        point_notes = request.POST.getlist('point_notes[]')

        for i, addr in enumerate(addresses):
            if addr.strip() and lats[i] and lngs[i]:
                DeliveryPoint.objects.create(
                    route=route,
                    order_number=order_numbers[i] if i < len(order_numbers) else f'#{i+1}',
                    address=addr,
                    lat=float(lats[i]),
                    lng=float(lngs[i]),
                    recipient_name=recipient_names[i] if i < len(recipient_names) else '',
                    recipient_phone=recipient_phones[i] if i < len(recipient_phones) else '',
                    notes=point_notes[i] if i < len(point_notes) else '',
                )

        return redirect('routes:detail', pk=route.pk)

    return render(request, 'routes/create.html', {'couriers': couriers})


def route_detail(request, pk):
    route = get_object_or_404(Route, pk=pk)
    points = route.delivery_points.all()
    return render(request, 'routes/detail.html', {'route': route, 'points': points})


@require_POST
def plan_with_ai(request, pk):
    route = get_object_or_404(Route, pk=pk)
    points = list(route.delivery_points.all())
    language = request.session.get('language', 'en')

    if not points:
        return JsonResponse({'error': 'No delivery points'}, status=400)

    # Build prompt based on language
    lang_prompts = {
        'en': {
            'system': 'You are an expert route optimization assistant for couriers in Uzbekistan. Always respond in English.',
            'user': f"""Plan the optimal delivery route for courier "{route.courier.name}" ({route.courier.get_vehicle_display()}).

Starting location: {route.courier_start_address or 'Unknown'} (lat: {route.courier_start_lat}, lng: {route.courier_start_lng})

Delivery points:
{chr(10).join([f'{i+1}. Order #{p.order_number} - {p.address} (lat: {p.lat}, lng: {p.lng}) - Recipient: {p.recipient_name or "N/A"}' for i, p in enumerate(points)])}

Please provide:
1. The optimal order to visit these delivery points (minimize backtracking and distance)
2. Brief reasoning for your suggested route
3. Estimated time savings compared to random order
4. Any important tips for this route

Respond in a clear, structured format."""
        },
        'ru': {
            'system': 'Вы эксперт по оптимизации маршрутов для курьеров в Узбекистане. Всегда отвечайте на русском языке.',
            'user': f"""Спланируйте оптимальный маршрут доставки для курьера "{route.courier.name}" ({route.courier.get_vehicle_display()}).

Начальная точка: {route.courier_start_address or 'Не указано'} (широта: {route.courier_start_lat}, долгота: {route.courier_start_lng})

Точки доставки:
{chr(10).join([f'{i+1}. Заказ #{p.order_number} - {p.address} (широта: {p.lat}, долгота: {p.lng}) - Получатель: {p.recipient_name or "Не указан"}' for i, p in enumerate(points)])}

Пожалуйста, укажите:
1. Оптимальный порядок посещения точек доставки (минимизация холостых поездок и расстояния)
2. Краткое обоснование предложенного маршрута
3. Примерная экономия времени по сравнению с произвольным порядком
4. Важные советы для этого маршрута

Ответьте в чётком структурированном формате."""
        },
        'uz': {
            'system': "Siz O'zbekistonda kuryer yo'nalishlarini optimallashtirish bo'yicha mutaxasssissiz. Har doim o'zbek tilida javob bering.",
            'user': f""""{route.courier.name}" kuryeri ({route.courier.get_vehicle_display()}) uchun optimal yetkazib berish yo'nalishini rejalashtiring.

Boshlang'ich nuqta: {route.courier_start_address or 'Noma\'lum'} (kenglik: {route.courier_start_lat}, uzunlik: {route.courier_start_lng})

Yetkazib berish nuqtalari:
{chr(10).join([f'{i+1}. Buyurtma #{p.order_number} - {p.address} (kenglik: {p.lat}, uzunlik: {p.lng}) - Qabul qiluvchi: {p.recipient_name or "Noma\'lum"}' for i, p in enumerate(points)])}

Iltimos, quyidagilarni ko'rsating:
1. Yetkazib berish nuqtalarini tashrif buyurish uchun optimal tartib (ortiqcha yo'l yurishni kamaytirish)
2. Taklif etilgan yo'nalish uchun qisqacha asoslash
3. Tasodifiy tartibga nisbatan taxminiy vaqt tejash
4. Bu yo'nalish uchun muhim maslahatlar

Aniq, tuzilgan formatda javob bering."""
        }
    }

    lang = language if language in lang_prompts else 'en'
    prompt_data = lang_prompts[lang]

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'http://localhost:8000',
                'X-Title': 'Courier Route Planner',
            },
            json={
                'model': settings.OPENROUTER_MODEL,
                'messages': [
                    {'role': 'system', 'content': prompt_data['system']},
                    {'role': 'user', 'content': prompt_data['user']},
                ],
                'max_tokens': 1500,
                'temperature': 0.3,
            },
            timeout=60
        )

        data = response.json()

        if 'choices' in data and data['choices']:
            ai_text = data['choices'][0]['message']['content']
            route.ai_response = ai_text
            route.language = lang
            route.status = 'in_progress'
            route.save()
            return JsonResponse({'success': True, 'response': ai_text})
        else:
            error_msg = data.get('error', {}).get('message', 'Unknown error from AI')
            return JsonResponse({'error': error_msg}, status=500)

    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'AI request timed out. Please try again.'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_couriers(request):
    couriers = Courier.objects.filter(is_active=True).values(
        'id', 'name', 'phone', 'vehicle',
        'default_start_lat', 'default_start_lng', 'default_start_address'
    )
    return JsonResponse({'couriers': list(couriers)})


def get_courier_location(request, pk):
    courier = get_object_or_404(Courier, pk=pk)
    return JsonResponse({
        'id': courier.id,
        'name': courier.name,
        'default_start_lat': courier.default_start_lat,
        'default_start_lng': courier.default_start_lng,
        'default_start_address': courier.default_start_address,
    })
