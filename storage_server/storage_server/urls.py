from django.urls import path, include
from .config import DB_HOST

urlpatterns = [
    path(f'${DB_HOST}/', include('storage_server.accounts.urls')),
    path(f'${DB_HOST}/files/', include('storage_server.files.urls')),
]
