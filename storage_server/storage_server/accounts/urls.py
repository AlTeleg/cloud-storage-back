from django.urls import path
from . import views

urlpatterns = [
    path('', views.RedirectView, name='redirect'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView, name='logout'),
    path('home/', views.HomeView, name='home'),
    path('admin/', views.AdminView, name='admin'),
    path('admin/files/', views.AllFilesAdminView, name='admin-files'),
    path('admin/create-user/', views.CreateUserAdminView.as_view(), name='admin-create-user'),
    path('admin/users/', views.AllUsersAdminView, name='admin-users'),
    path('admin/users/<int:user_id>', views.DeleteUserAdminView, name='admin-users')
]