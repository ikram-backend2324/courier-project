import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Courier, Route, DeliveryPoint


def get_courier_for_user(user):
    """Returns courier linked to user, or None if admin/no link."""
    if user.is_staff or user.is_superuser:
        return None
    try:
        return Courier.objects.get(user=user)
    except Courier.DoesNotExist:
        return None


@login_required(login_url='/login/')
def route_list(request):
    user = request.user
    courier = get_courier_for_user(user)
    if courier:
        routes = Route.objects.select_related('courier').filter(courier=courier)
    else:
        routes = Route.objects.select_related('courier').all()
    couriers = Courier.objects.filter(is_active=True)
    return render(request, 'routes/list.html', {'routes': routes, 'couriers': couriers})


@login_required(login_url='/login/')
def route_create(request):
    user = request.user
    courier_for_user = get_courier_for_user(user)
    # Couriers can only create routes for themselves
    if courier_for_user:
        couriers = Courier.objects.filter(id=courier_for_user.id)
    else:
        couriers = Courier.objects.filter(is_active=True)

    if request.method == 'POST':
        courier_id = request.POST.get('courier')
        title = request.POST.get('title')
        notes = request.POST.get('notes', '')
        courier_start_lat = request.POST.get('courier_start_lat')
        courier_start_lng = request.POST.get('courier_start_lng')
        courier_start_address = request.POST.get('courier_start_address', '')
        language = request.session.get('language', 'en')

        # Security: couriers can only create routes for themselves
        if courier_for_user:
            courier = courier_for_user
        else:
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
                    order_number=order_numbers[i] if i < len(order_numbers) else '#' + str(i + 1),
                    address=addr,
                    lat=float(lats[i]),
                    lng=float(lngs[i]),
                    recipient_name=recipient_names[i] if i < len(recipient_names) else '',
                    recipient_phone=recipient_phones[i] if i < len(recipient_phones) else '',
                    notes=point_notes[i] if i < len(point_notes) else '',
                )

        return redirect('routes:detail', pk=route.pk)

    return render(request, 'routes/create.html', {
        'couriers': couriers,
        'is_courier': courier_for_user is not None,
        'courier_for_user': courier_for_user,
    })


@login_required(login_url='/login/')
def route_detail(request, pk):
    user = request.user
    courier = get_courier_for_user(user)
    route = get_object_or_404(Route, pk=pk)
    # Couriers can only see their own routes
    if courier and route.courier != courier:
        return redirect('routes:list')
    points = route.delivery_points.all()
    return render(request, 'routes/detail.html', {'route': route, 'points': points})


@login_required(login_url='/login/')
@require_POST
def plan_with_ai(request, pk):
    user = request.user
    courier = get_courier_for_user(user)
    route = get_object_or_404(Route, pk=pk)
    if courier and route.courier != courier:
        return JsonResponse({'error': 'Access denied'}, status=403)

    points = list(route.delivery_points.all())
    language = request.session.get('language', 'en')

    if not points:
        return JsonResponse({'error': 'No delivery points'}, status=400)

    points_en_lines = []
    points_ru_lines = []
    points_uz_lines = []
    for i, p in enumerate(points):
        recipient_en = p.recipient_name if p.recipient_name else 'N/A'
        recipient_ru = p.recipient_name if p.recipient_name else 'Не указан'
        recipient_uz = p.recipient_name if p.recipient_name else "Noma'lum"
        points_en_lines.append(
            str(i + 1) + '. Order #' + p.order_number + ' - ' + p.address +
            ' (lat: ' + str(p.lat) + ', lng: ' + str(p.lng) + ') - Recipient: ' + recipient_en
        )
        points_ru_lines.append(
            str(i + 1) + '. Заказ #' + p.order_number + ' - ' + p.address +
            ' (широта: ' + str(p.lat) + ', долгота: ' + str(p.lng) + ') - Получатель: ' + recipient_ru
        )
        points_uz_lines.append(
            str(i + 1) + '. Buyurtma #' + p.order_number + ' - ' + p.address +
            ' (kenglik: ' + str(p.lat) + ', uzunlik: ' + str(p.lng) + ') - Qabul qiluvchi: ' + recipient_uz
        )

    points_en = '\n'.join(points_en_lines)
    points_ru = '\n'.join(points_ru_lines)
    points_uz = '\n'.join(points_uz_lines)

    start_address = route.courier_start_address or 'Unknown'
    start_address_ru = route.courier_start_address or 'Не указано'
    start_address_uz = route.courier_start_address or "Noma'lum"

    lang_prompts = {
        'en': {
            'system': 'You are an expert route optimization assistant for couriers in Uzbekistan. Always respond in English.',
            'user': (
                'Plan the optimal delivery route for courier "' + route.courier.name + '" (' + route.courier.get_vehicle_display() + ').\n\n'
                'Starting location: ' + start_address + ' (lat: ' + str(route.courier_start_lat) + ', lng: ' + str(route.courier_start_lng) + ')\n\n'
                'Delivery points:\n' + points_en + '\n\n'
                'Please provide:\n'
                '1. The optimal order to visit these delivery points (minimize backtracking and distance)\n'
                '2. Brief reasoning for your suggested route\n'
                '3. Estimated time savings compared to random order\n'
                '4. Any important tips for this route\n\n'
                'Respond in a clear, structured format.'
            ),
        },
        'ru': {
            'system': 'Вы эксперт по оптимизации маршрутов для курьеров в Узбекистане. Всегда отвечайте на русском языке.',
            'user': (
                'Спланируйте оптимальный маршрут доставки для курьера "' + route.courier.name + '" (' + route.courier.get_vehicle_display() + ').\n\n'
                'Начальная точка: ' + start_address_ru + ' (широта: ' + str(route.courier_start_lat) + ', долгота: ' + str(route.courier_start_lng) + ')\n\n'
                'Точки доставки:\n' + points_ru + '\n\n'
                'Пожалуйста, укажите:\n'
                '1. Оптимальный порядок посещения точек доставки (минимизация холостых поездок и расстояния)\n'
                '2. Краткое обоснование предложенного маршрута\n'
                '3. Примерная экономия времени по сравнению с произвольным порядком\n'
                '4. Важные советы для этого маршрута\n\n'
                'Ответьте в чётком структурированном формате.'
            ),
        },
        'uz': {
            'system': "Siz O'zbekistonda kuryer yo'nalishlarini optimallashtirish bo'yicha mutaxasssissiz. Har doim o'zbek tilida javob bering.",
            'user': (
                '"' + route.courier.name + '" kuryeri (' + route.courier.get_vehicle_display() + ") uchun optimal yetkazib berish yo'nalishini rejalashtiring.\n\n"
                "Boshlang'ich nuqta: " + start_address_uz + ' (kenglik: ' + str(route.courier_start_lat) + ', uzunlik: ' + str(route.courier_start_lng) + ')\n\n'
                "Yetkazib berish nuqtalari:\n" + points_uz + '\n\n'
                "Iltimos, quyidagilarni ko'rsating:\n"
                "1. Yetkazib berish nuqtalarini tashrif buyurish uchun optimal tartib (ortiqcha yo'l yurishni kamaytirish)\n"
                "2. Taklif etilgan yo'nalish uchun qisqacha asoslash\n"
                '3. Tasodifiy tartibga nisbatan taxminiy vaqt tejash\n'
                "4. Bu yo'nalish uchun muhim maslahatlar\n\n"
                'Aniq, tuzilgan formatda javob bering.'
            ),
        },
    }

    lang = language if language in lang_prompts else 'en'
    prompt_data = lang_prompts[lang]

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': 'Bearer ' + settings.OPENROUTER_API_KEY,
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


@login_required(login_url='/login/')
def get_couriers(request):
    couriers = Courier.objects.filter(is_active=True).values(
        'id', 'name', 'phone', 'vehicle',
        'default_start_lat', 'default_start_lng', 'default_start_address'
    )
    return JsonResponse({'couriers': list(couriers)})


@login_required(login_url='/login/')
def get_courier_location(request, pk):
    courier = get_object_or_404(Courier, pk=pk)
    return JsonResponse({
        'id': courier.id,
        'name': courier.name,
        'default_start_lat': courier.default_start_lat,
        'default_start_lng': courier.default_start_lng,
        'default_start_address': courier.default_start_address,
    })
