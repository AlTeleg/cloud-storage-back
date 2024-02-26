from django.db import models
from accounts.models import User

class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_name = models.CharField(max_length=255)
    size = models.IntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    last_download_date = models.DateTimeField(auto_now=True)
    comment = models.TextField()
    path = models.CharField(max_length=255)
    special_link = models.CharField(max_length=255)

    def __str__(self):
        return self.original_name