from django.contrib import admin
from django.utils.html import format_html
from .models import Courier, Route, DeliveryPoint


class DeliveryPointInline(admin.TabularInline):
    model = DeliveryPoint
    extra = 1
    fields = ['order_number', 'address', 'lat', 'lng', 'recipient_name', 'recipient_phone', 'status', 'optimized_sequence']
    readonly_fields = ['optimized_sequence']


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'vehicle', 'user', 'default_start_address', 'is_active', 'route_count']
    list_filter = ['vehicle', 'is_active']
    search_fields = ['name', 'phone', 'user__username']
    list_editable = ['is_active']
    fieldsets = (
        ('Courier Info', {
            'fields': ('name', 'phone', 'vehicle', 'is_active')
        }),
        ('Login Account', {
            'fields': ('user',),
            'description': 'Link a Django user account so this courier can log in to the client side.'
        }),
        ('Default Starting Location', {
            'fields': ('default_start_address', 'default_start_lat', 'default_start_lng'),
            'description': 'Set the default starting location (e.g. warehouse).'
        }),
    )

    def route_count(self, obj):
        count = obj.routes.count()
        return format_html('<span style="font-weight:bold;color:#007bff">{}</span>', count)
    route_count.short_description = 'Total Routes'


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['title', 'courier', 'status', 'language', 'point_count', 'created_at']
    list_filter = ['status', 'language', 'courier', 'created_at']
    search_fields = ['title', 'courier__name']
    readonly_fields = ['ai_response', 'ai_optimized_order', 'created_at', 'updated_at']
    inlines = [DeliveryPointInline]
    fieldsets = (
        ('Route Info', {
            'fields': ('title', 'courier', 'status', 'language', 'notes')
        }),
        ('Courier Starting Location', {
            'fields': ('courier_start_address', 'courier_start_lat', 'courier_start_lng'),
        }),
        ('AI Results', {
            'fields': ('ai_response', 'ai_optimized_order'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def point_count(self, obj):
        count = obj.delivery_points.count()
        return format_html('<span style="font-weight:bold;color:#28a745">{} points</span>', count)
    point_count.short_description = 'Delivery Points'


@admin.register(DeliveryPoint)
class DeliveryPointAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'address', 'route', 'recipient_name', 'status', 'optimized_sequence']
    list_filter = ['status', 'route__courier']
    search_fields = ['order_number', 'address', 'recipient_name']
    list_editable = ['status']
