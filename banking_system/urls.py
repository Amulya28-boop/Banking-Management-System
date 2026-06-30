from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # ✅ HOME ROUTING (IMPORTANT)
    path('', include('bank.urls')),
]