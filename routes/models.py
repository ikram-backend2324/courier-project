from django.db import models


class Courier(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    vehicle = models.CharField(max_length=50, choices=[
        ('bike', 'Bike'),
        ('motorcycle', 'Motorcycle'),
        ('car', 'Car'),
        ('foot', 'On Foot'),
    ], default='motorcycle')
    default_start_lat = models.FloatField(null=True, blank=True, help_text="Default starting latitude (e.g. warehouse)")
    default_start_lng = models.FloatField(null=True, blank=True, help_text="Default starting longitude (e.g. warehouse)")
    default_start_address = models.CharField(max_length=255, blank=True, help_text="Default starting address description")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_vehicle_display()})"

    class Meta:
        ordering = ['name']


class Route(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    courier = models.ForeignKey(Courier, on_delete=models.CASCADE, related_name='routes')
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    courier_start_lat = models.FloatField(null=True, blank=True)
    courier_start_lng = models.FloatField(null=True, blank=True)
    courier_start_address = models.CharField(max_length=255, blank=True)
    ai_response = models.TextField(blank=True)
    ai_optimized_order = models.TextField(blank=True, help_text="JSON list of optimized point IDs")
    language = models.CharField(max_length=5, default='en', choices=[('en','English'),('ru','Russian'),('uz','Uzbek')])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.courier.name}"

    class Meta:
        ordering = ['-created_at']


class DeliveryPoint(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='delivery_points')
    order_number = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    lat = models.FloatField()
    lng = models.FloatField()
    recipient_name = models.CharField(max_length=100, blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    optimized_sequence = models.IntegerField(null=True, blank=True, help_text="AI suggested visit order")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.order_number} - {self.address}"

    class Meta:
        ordering = ['optimized_sequence', 'id']
