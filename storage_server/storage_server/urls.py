from django.urls import path, include

urlpatterns = [
    path('', include('storage_server.accounts.urls')),
    path('/files/', include('storage_server.files.urls')),
]
