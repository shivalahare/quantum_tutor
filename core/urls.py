from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tutor.urls')),
    path('', include('tutor.urls')),

    # Redirect login to admin login for now
    path('accounts/login/', RedirectView.as_view(url='/admin/login/?next=/', permanent=False)),
    path('accounts/logout/', RedirectView.as_view(url='/admin/logout/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)