from django.urls import path
from . import views

urlpatterns = [
    path('', views.RedirectView.as_view(), name='redirect'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('home/', views.HomeView.as_view(), name='home'),
    path('admin/', views.AdminView.as_view(), name='admin'),
    path('admin/files/', views.AllFilesAdminView.as_view(), name='admin-files'),
    path('admin/files/get/', views.GetFilesAdminView.as_view(), name='admin-get-files'),
    path('admin/create-user/', views.CreateUserAdminView.as_view(), name='admin-create-user'),
    path('admin/users/', views.AllUsersAdminView.as_view(), name='admin-users'),
    path('admin/users/get/', views.GetUsersAdminView.as_view(), name='admin-get-users'),
    path('admin/users/<int:user_id>/', views.ChangeUserAdminView.as_view(), name='admin-change-user')
]
