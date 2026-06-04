from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.admin_site.urls if hasattr(admin.site, 'admin_site') else admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('vulnerabilities.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
