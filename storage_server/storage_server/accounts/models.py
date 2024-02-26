from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')

        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

    def create_admin(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', False)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True, blank=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    storage_path = models.CharField(max_length=255)

    USERNAME_FIELD = 'username'

    objects = UserManager()

    def __str__(self):
        return str(self.id)
