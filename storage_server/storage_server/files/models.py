from django.db import models
from ..accounts.models import User
from hashlib import sha256
import secrets


class File(models.Model):
    file_data = models.BinaryField()
    user = models.ForeignKey(User, related_name='files', on_delete=models.CASCADE)
    original_name = models.CharField(max_length=50)
    name = models.CharField(max_length=70, default=original_name)
    size = models.IntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    last_download_date = models.DateTimeField(auto_now=True)
    comment = models.TextField()
    path = models.CharField(max_length=50)
    special_link = models.CharField(max_length=255)
    recipients = models.ManyToManyField(User, related_name='shared_files')

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.original_name
        if not self.special_link:
            token = sha256(secrets.token_bytes(16)).hexdigest()
            self.special_link = f'/files/{self.pk}/download/{token}/'
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.original_name
