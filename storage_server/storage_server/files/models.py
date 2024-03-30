from django.db import models
from ..accounts.models import User
from hashlib import sha256
import secrets
import os
from django.conf import settings


class File(models.Model):
    data = models.BinaryField()
    user = models.ForeignKey(User, related_name='files', on_delete=models.CASCADE)
    original_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100, null=True)
    size = models.IntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    last_download_date = models.DateTimeField(null=True)
    comment = models.TextField(max_length=200)
    path = models.CharField(max_length=100)
    special_link = models.CharField(max_length=255)
    recipients = models.ManyToManyField(User, related_name='shared_files')

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.original_name
        super().save(*args, **kwargs)
        if not self.special_link:
            token = sha256(secrets.token_bytes(16)).hexdigest()
            self.path = os.path.join(settings.MEDIA_ROOT, str(self.user.id), self.original_name)
            self.special_link = f'/files/{self.id}/download/{token}/'
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        os.remove(os.path.join(settings.MEDIA_ROOT, str(self.user.id), self.original_name))
        super(File, self).delete(*args, **kwargs)
