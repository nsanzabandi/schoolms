# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.urls import reverse_lazy

def redirect_to_login(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return redirect('accounts:login')

urlpatterns = [
    path('', redirect_to_login, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),  # Simplified include
]

# Add static/media serving for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)