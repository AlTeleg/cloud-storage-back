from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path(f'${settings.HOST}/', include('storage_server.accounts.urls')),
    path(f'${settings.HOST}/files/', include('storage_server.files.urls')),
]
