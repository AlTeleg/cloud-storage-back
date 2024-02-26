from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.ListView, name='file-list'),
    path('upload/', views.UploadView, name='file-upload'),
    path('<int:file_id>/', views.DetailView, name='file-detail'),
    path('<int:file_id>/delete/', views.DeleteView, name='file-delete'),
    path('<int:file_id>/rename/', views.RenameView, name='file-rename'),
    path('<int:file_id>/comment/', views.CommentView, name='file-comment'),
    path('<int:file_id>/download/', views.DownloadView, name='file-download'),
    path('<int:file_id>/share/', views.UserShareView, name='file-share'),
    re_path(r'^files/(?P<special_link>.+)/$', views.DownloadSpecialView.as_view(), name='download-special')
]