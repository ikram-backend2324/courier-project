from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Courier Route AI Admin"
admin.site.site_title = "Courier Route AI"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('routes/', include('routes.urls')),
]
