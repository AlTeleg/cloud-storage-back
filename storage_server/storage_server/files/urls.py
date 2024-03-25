from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.ListView.as_view(), name='file-list'),
    path('get/', views.GetFilesView.as_view(), name='files-get'),
    path('upload/', views.UploadView.as_view(), name='file-upload'),
    path('<int:file_id>/', views.DetailView.as_view(), name='file-detail'),
    path('<int:file_id>/get/', views.GetFileView.as_view(), name='file-get'),
    path('<int:file_id>/delete/', views.DeleteView.as_view(), name='file-delete'),
    path('<int:file_id>/rename/', views.RenameView.as_view(), name='file-rename'),
    path('<int:file_id>/comment/', views.CommentView.as_view(), name='file-comment'),
    path('<int:file_id>/download/', views.DownloadView.as_view(), name='file-download'),
    path('<int:file_id>/share/', views.UserShareView.as_view(), name='file-share'),
    re_path(r'^files/(?P<file_id>\d+)/(?P<token>[a-fA-F0-9]{32})/$', views.DownloadSpecialView.as_view(),
            name='download-special')
]
