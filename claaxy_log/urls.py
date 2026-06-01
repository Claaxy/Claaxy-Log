from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'accounts/login/',
        RedirectView.as_view(url='/accounts/google/login/', permanent=False),
        name='account_login_redirect',
    ),
    path('accounts/signup/', RedirectView.as_view(url='/accounts/google/login/', permanent=False)),
    path('accounts/', include('allauth.urls')),
    path('', include('apps.core.urls')),
    path('projects/', include('apps.projects.urls')),
    path('users/', include('apps.users.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
