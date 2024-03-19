from django.db import models
from ..accounts.models import User
from hashlib import sha256
import secrets


class File(models.Model):
    data = models.BinaryField()
    user = models.ForeignKey(User, related_name='files', on_delete=models.CASCADE)
    original_name = models.CharField(max_length=70)
    name = models.CharField(max_length=70, null=True)
    size = models.IntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    last_download_date = models.DateTimeField(null=True)
    comment = models.TextField(max_length=200)
    path = models.CharField(max_length=50)
    special_link = models.CharField(max_length=255)
    recipients = models.ManyToManyField(User, related_name='shared_files')

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.original_name
        if not self.special_link:
            token = sha256(secrets.token_bytes(16)).hexdigest()
            self.special_link = f'/files/{self.pk}/download/{token}/'
        super().save(*args, **kwargs)
