from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from routes.models import Courier, Route, DeliveryPoint


class Command(BaseCommand):
    help = 'Seed the database with default couriers, users and sample routes'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding database...')

        # Create superuser/admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@routeai.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('✅ Admin created: admin / admin123'))
        else:
            self.stdout.write('⏭️  Admin already exists')

        # Create courier users and couriers
        couriers_data = [
            {
                'username': 'jasur',
                'password': 'courier123',
                'name': 'Jasur Toshmatov',
                'phone': '+998 90 123 4567',
                'vehicle': 'motorcycle',
                'start_lat': 41.2990,
                'start_lng': 69.2401,
                'start_address': 'Main Warehouse, Mirzo Ulugbek, Tashkent',
            },
            {
                'username': 'bobur',
                'password': 'courier123',
                'name': 'Bobur Rahimov',
                'phone': '+998 91 234 5678',
                'vehicle': 'bike',
                'start_lat': 41.3111,
                'start_lng': 69.2797,
                'start_address': 'Depot, Yunusabad, Tashkent',
            },
            {
                'username': 'dilnoza',
                'password': 'courier123',
                'name': 'Dilnoza Nazarova',
                'phone': '+998 93 345 6789',
                'vehicle': 'car',
                'start_lat': 41.2830,
                'start_lng': 69.2000,
                'start_address': 'South Depot, Chilanzar, Tashkent',
            },
        ]

        created_couriers = []
        for cd in couriers_data:
            user, user_created = User.objects.get_or_create(username=cd['username'])
            if user_created:
                user.set_password(cd['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    '✅ User created: ' + cd['username'] + ' / ' + cd['password']
                ))

            courier, c_created = Courier.objects.get_or_create(
                name=cd['name'],
                defaults={
                    'user': user,
                    'phone': cd['phone'],
                    'vehicle': cd['vehicle'],
                    'default_start_lat': cd['start_lat'],
                    'default_start_lng': cd['start_lng'],
                    'default_start_address': cd['start_address'],
                    'is_active': True,
                }
            )
            if not c_created and courier.user is None:
                courier.user = user
                courier.save()

            created_couriers.append(courier)
            if c_created:
                self.stdout.write(self.style.SUCCESS('✅ Courier created: ' + courier.name))
            else:
                self.stdout.write('⏭️  Courier already exists: ' + courier.name)

        # Create sample routes with delivery points
        sample_routes = [
            {
                'courier': created_couriers[0],
                'title': 'Morning Delivery - Tashkent Center',
                'status': 'pending',
                'start_lat': 41.2990,
                'start_lng': 69.2401,
                'start_address': 'Main Warehouse, Mirzo Ulugbek',
                'points': [
                    {'order': 'ORD-001', 'address': 'Chilanzar, Bunyodkor street 12', 'lat': 41.2830, 'lng': 69.2000, 'recipient': 'Ahmad Karimov', 'phone': '+998901234567'},
                    {'order': 'ORD-002', 'address': 'Yunusabad, block 7, apt 45', 'lat': 41.3200, 'lng': 69.2900, 'recipient': 'Malika Yusupova', 'phone': '+998912345678'},
                    {'order': 'ORD-003', 'address': 'Mirzo Ulugbek, Yangi Shahar 22', 'lat': 41.3100, 'lng': 69.3100, 'recipient': 'Sardor Aliyev', 'phone': '+998935678901'},
                ],
            },
            {
                'courier': created_couriers[1],
                'title': 'Afternoon Route - Yunusabad',
                'status': 'in_progress',
                'start_lat': 41.3111,
                'start_lng': 69.2797,
                'start_address': 'Depot, Yunusabad',
                'points': [
                    {'order': 'ORD-004', 'address': 'Yunusabad 17, house 3', 'lat': 41.3250, 'lng': 69.2850, 'recipient': 'Nodira Hasanova', 'phone': '+998907654321'},
                    {'order': 'ORD-005', 'address': 'Shaykhantahur, Amir Temur 55', 'lat': 41.3050, 'lng': 69.2600, 'recipient': 'Ulugbek Mirzayev', 'phone': '+998901111222'},
                ],
            },
            {
                'courier': created_couriers[2],
                'title': 'Express Delivery - Chilanzar',
                'status': 'completed',
                'start_lat': 41.2830,
                'start_lng': 69.2000,
                'start_address': 'South Depot, Chilanzar',
                'points': [
                    {'order': 'ORD-006', 'address': 'Chilanzar 3, apt 12', 'lat': 41.2780, 'lng': 69.1950, 'recipient': 'Zulfiya Rашидова', 'phone': '+998993334455'},
                    {'order': 'ORD-007', 'address': 'Sergeli, New buildings block 5', 'lat': 41.2500, 'lng': 69.2100, 'recipient': 'Bahodir Nazarov', 'phone': '+998905556677'},
                    {'order': 'ORD-008', 'address': 'Almazar, Dustlik 88', 'lat': 41.3300, 'lng': 69.2200, 'recipient': 'Kamola Ibragimova', 'phone': '+998917778899'},
                ],
            },
        ]

        for rd in sample_routes:
            if not Route.objects.filter(title=rd['title']).exists():
                route = Route.objects.create(
                    courier=rd['courier'],
                    title=rd['title'],
                    status=rd['status'],
                    courier_start_lat=rd['start_lat'],
                    courier_start_lng=rd['start_lng'],
                    courier_start_address=rd['start_address'],
                    language='en',
                )
                for i, pt in enumerate(rd['points']):
                    DeliveryPoint.objects.create(
                        route=route,
                        order_number=pt['order'],
                        address=pt['address'],
                        lat=pt['lat'],
                        lng=pt['lng'],
                        recipient_name=pt['recipient'],
                        recipient_phone=pt['phone'],
                        status='delivered' if rd['status'] == 'completed' else 'pending',
                    )
                self.stdout.write(self.style.SUCCESS(
                    '✅ Route created: ' + rd['title'] + ' (' + str(len(rd['points'])) + ' points)'
                ))
            else:
                self.stdout.write('⏭️  Route already exists: ' + rd['title'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Seeding complete!'))
        self.stdout.write('')
        self.stdout.write('👤 Login accounts:')
        self.stdout.write('   admin     / admin123   (Manager - full access)')
        self.stdout.write('   jasur     / courier123 (Courier)')
        self.stdout.write('   bobur     / courier123 (Courier)')
        self.stdout.write('   dilnoza   / courier123 (Courier)')
